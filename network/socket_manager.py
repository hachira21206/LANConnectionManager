"""TCP Server/Client and UDP Manager with Qt signals for thread-safe UI."""
import socket
import json
import threading
import struct
import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict
from pathlib import Path

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


# ─── TCP Server ──────────────────────────────────────────────────────

class TCPServer(QThread):
    """Multi-client TCP server running in a background thread.

    Signals:
        client_connected: (client_address: str)
        client_disconnected: (client_address: str)
        message_received: (client_address: str, message: str)
        server_started: (port: int)
        server_stopped: ()
        server_error: (error_message: str)
        status_changed: (status: str)
    """

    client_connected = Signal(str)
    client_disconnected = Signal(str)
    message_received = Signal(str, str)
    server_started = Signal(int)
    server_stopped = Signal()
    server_error = Signal(str)
    status_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port: int = 5000
        self._host: str = "0.0.0.0"
        self._running: bool = False
        self._server_socket: Optional[socket.socket] = None
        self._clients: Dict[str, socket.socket] = {}
        self._clients_lock = threading.Lock()
        self._max_clients: int = 20
        self._buffer_size: int = 4096

    def configure(self, port: int = 5000, host: str = "0.0.0.0",
                  max_clients: int = 20, buffer_size: int = 4096) -> None:
        """Configure server parameters."""
        self._port = port
        self._host = host
        self._max_clients = max_clients
        self._buffer_size = buffer_size

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def client_list(self) -> list:
        return list(self._clients.keys())

    def stop(self) -> None:
        """Stop the server gracefully."""
        self._running = False
        # Close server socket to unblock accept()
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def send_to_client(self, client_addr: str, message: str) -> bool:
        """Send message to a specific client.

        Args:
            client_addr: Client address string.
            message: Message to send.

        Returns:
            True if sent successfully.
        """
        with self._clients_lock:
            client_sock = self._clients.get(client_addr)
        if client_sock:
            try:
                data = message.encode('utf-8')
                client_sock.sendall(data)
                return True
            except (OSError, BrokenPipeError) as e:
                logger.error("Error sending to %s: %s", client_addr, e)
                self._remove_client(client_addr)
        return False

    def broadcast(self, message: str, exclude: Optional[str] = None) -> None:
        """Broadcast message to all connected clients.

        Args:
            message: Message to broadcast.
            exclude: Client address to exclude.
        """
        with self._clients_lock:
            addrs = list(self._clients.keys())
        for addr in addrs:
            if addr != exclude:
                self.send_to_client(addr, message)

    def run(self) -> None:
        """Main server loop."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.settimeout(1.0)
            self._server_socket.bind((self._host, self._port))
            self._server_socket.listen(self._max_clients)
            self._running = True

            self.server_started.emit(self._port)
            self.status_changed.emit("RUNNING")
            logger.info("TCP Server started on %s:%d", self._host, self._port)

            with ThreadPoolExecutor(max_workers=self._max_clients) as executor:
                while self._running:
                    try:
                        client_socket, addr = self._server_socket.accept()
                        client_addr = f"{addr[0]}:{addr[1]}"
                        with self._clients_lock:
                            self._clients[client_addr] = client_socket
                        self.client_connected.emit(client_addr)
                        logger.info("Client connected: %s", client_addr)

                        executor.submit(self._handle_client, client_socket, client_addr)

                    except socket.timeout:
                        continue
                    except OSError:
                        if self._running:
                            logger.error("Server socket error")
                        break

        except OSError as e:
            error_msg = f"Server error: {str(e)}"
            if "Address already in use" in str(e) or "10048" in str(e):
                error_msg = f"Port {self._port} is already in use"
            self.server_error.emit(error_msg)
            logger.error(error_msg)
        finally:
            self._cleanup()

    def _handle_client(self, client_socket: socket.socket, client_addr: str) -> None:
        """Handle communication with a single client.

        Args:
            client_socket: Client socket.
            client_addr: Client address string.
        """
        client_socket.settimeout(None)

        try:
            while self._running:
                with self._clients_lock:
                    if client_addr not in self._clients:
                        break
                try:
                    data = client_socket.recv(self._buffer_size)
                    if not data:
                        break  # Client disconnected

                    message = data.decode('utf-8', errors='replace')
                    self.message_received.emit(client_addr, message)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except OSError:
                    break
        finally:
            self._remove_client(client_addr)

    def _remove_client(self, client_addr: str) -> None:
        """Remove and clean up a client connection."""
        with self._clients_lock:
            client_sock = self._clients.pop(client_addr, None)
        if client_sock:
            try:
                client_sock.close()
            except OSError:
                pass
            self.client_disconnected.emit(client_addr)
            logger.info("Client disconnected: %s", client_addr)

    def _cleanup(self) -> None:
        """Clean up all connections."""
        self._running = False
        with self._clients_lock:
            addrs = list(self._clients.keys())
        for addr in addrs:
            self._remove_client(addr)
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None
        self.server_stopped.emit()
        self.status_changed.emit("STOPPED")
        logger.info("TCP Server stopped")


# ─── TCP Client ──────────────────────────────────────────────────────

class TCPClient(QThread):
    """TCP client running in a background thread.

    Signals:
        connected: (server_address: str)
        disconnected: ()
        message_received: (message: str)
        connection_error: (error_message: str)
        status_changed: (status: str)
    """

    connected = Signal(str)
    disconnected = Signal()
    message_received = Signal(str)
    connection_error = Signal(str)
    status_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._host: str = ""
        self._port: int = 5000
        self._socket: Optional[socket.socket] = None
        self._running: bool = False
        self._buffer_size: int = 4096
        self._timeout: float = 5.0

    def configure(self, host: str, port: int,
                  timeout: float = 5.0, buffer_size: int = 4096) -> None:
        """Configure client connection parameters."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._buffer_size = buffer_size

    @property
    def is_connected(self) -> bool:
        return self._running and self._socket is not None

    def disconnect_from_server(self) -> None:
        """Disconnect from the server."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def send_message(self, message: str) -> bool:
        """Send a message to the server.

        Args:
            message: Message string to send.

        Returns:
            True if sent successfully.
        """
        if not self._socket or not self._running:
            return False
        try:
            self._socket.sendall(message.encode('utf-8'))
            return True
        except (OSError, BrokenPipeError) as e:
            self.connection_error.emit(f"Send error: {str(e)}")
            self.disconnect_from_server()
            return False

    def run(self) -> None:
        """Connect and listen for messages."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self._timeout)
            self._socket.connect((self._host, self._port))
            self._running = True
            self._socket.settimeout(1.0)  # For recv loop

            server_addr = f"{self._host}:{self._port}"
            self.connected.emit(server_addr)
            self.status_changed.emit("CONNECTED")
            logger.info("Connected to server %s", server_addr)

            while self._running:
                try:
                    data = self._socket.recv(self._buffer_size)
                    if not data:
                        break  # Server closed connection

                    message = data.decode('utf-8', errors='replace')
                    self.message_received.emit(message)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except OSError:
                    if self._running:
                        break

        except ConnectionRefusedError:
            self.connection_error.emit(
                f"Connection refused: {self._host}:{self._port}"
            )
            logger.warning("Connection refused: %s:%d", self._host, self._port)
        except socket.timeout:
            self.connection_error.emit(
                f"Connection timed out: {self._host}:{self._port}"
            )
        except OSError as e:
            self.connection_error.emit(f"Connection error: {str(e)}")
            logger.error("TCP Client error: %s", e)
        finally:
            self._running = False
            if self._socket:
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None
            self.disconnected.emit()
            self.status_changed.emit("DISCONNECTED")
            logger.info("Disconnected from server")


# ─── UDP Manager ─────────────────────────────────────────────────────

class UDPManager(QThread):
    """UDP send/receive manager.

    Signals:
        message_received: (sender_address: str, message: str)
        listener_started: (port: int)
        listener_stopped: ()
        send_success: (target: str)
        udp_error: (error_message: str)
    """

    message_received = Signal(str, str)
    listener_started = Signal(int)
    listener_stopped = Signal()
    send_success = Signal(str)
    udp_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port: int = 5001
        self._running: bool = False
        self._socket: Optional[socket.socket] = None
        self._buffer_size: int = 4096

    def configure(self, port: int = 5001, buffer_size: int = 4096) -> None:
        """Configure UDP listener."""
        self._port = port
        self._buffer_size = buffer_size

    @property
    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        """Stop the UDP listener."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def send_message(self, target_ip: str, target_port: int, message: str) -> bool:
        """Send a UDP message.

        Args:
            target_ip: Target IP address.
            target_port: Target port number.
            message: Message to send.

        Returns:
            True if sent successfully.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(2.0)
                sock.sendto(message.encode('utf-8'), (target_ip, target_port))
                self.send_success.emit(f"{target_ip}:{target_port}")
                return True
        except OSError as e:
            self.udp_error.emit(f"UDP send error: {str(e)}")
            logger.error("UDP send error: %s", e)
            return False

    def run(self) -> None:
        """UDP listener loop."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.settimeout(1.0)
            self._socket.bind(("0.0.0.0", self._port))
            self._running = True

            self.listener_started.emit(self._port)
            logger.info("UDP Listener started on port %d", self._port)

            while self._running:
                try:
                    data, addr = self._socket.recvfrom(self._buffer_size)
                    message = data.decode('utf-8', errors='replace')
                    sender = f"{addr[0]}:{addr[1]}"
                    self.message_received.emit(sender, message)

                except socket.timeout:
                    continue
                except OSError:
                    if self._running:
                        break

        except OSError as e:
            error_msg = f"UDP error: {str(e)}"
            if "10048" in str(e) or "Address already in use" in str(e):
                error_msg = f"Port {self._port} is already in use"
            self.udp_error.emit(error_msg)
            logger.error(error_msg)
        finally:
            self._running = False
            if self._socket:
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None
            self.listener_stopped.emit()
            logger.info("UDP Listener stopped")


# ─── File Transfer Server ────────────────────────────────────────────

class FileTransferServer(QThread):
    """Server for receiving files over TCP.

    Signals:
        transfer_started: (filename: str, file_size: int, sender: str)
        transfer_progress: (bytes_received: int, total: int)
        transfer_complete: (filename: str, save_path: str)
        transfer_error: (error_message: str)
        server_ready: (port: int)
        server_stopped: ()
    """

    transfer_started = Signal(str, int, str)
    transfer_progress = Signal(int, int)
    transfer_complete = Signal(str, str)
    transfer_error = Signal(str)
    server_ready = Signal(int)
    server_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port: int = 5003
        self._running: bool = False
        self._save_dir: str = str(Path.home() / "Downloads")
        self._chunk_size: int = 8192

    def configure(self, port: int = 5003, save_dir: str = "",
                  chunk_size: int = 8192) -> None:
        """Configure file transfer server."""
        self._port = port
        if save_dir:
            self._save_dir = save_dir
        self._chunk_size = chunk_size

    def stop(self) -> None:
        """Stop the file transfer server."""
        self._running = False

    def run(self) -> None:
        """Listen for incoming file transfers."""
        server_socket = None
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(1.0)
            server_socket.bind(("0.0.0.0", self._port))
            server_socket.listen(1)
            self._running = True

            self.server_ready.emit(self._port)
            logger.info("File transfer server listening on port %d", self._port)

            while self._running:
                try:
                    client_socket, addr = server_socket.accept()
                    sender = f"{addr[0]}:{addr[1]}"
                    self._receive_file(client_socket, sender)
                except socket.timeout:
                    continue
                except OSError:
                    if self._running:
                        break

        except OSError as e:
            self.transfer_error.emit(f"File server error: {str(e)}")
            logger.error("File server error: %s", e)
        finally:
            self._running = False
            if server_socket:
                try:
                    server_socket.close()
                except OSError:
                    pass
            self.server_stopped.emit()

    def _receive_file(self, client_socket: socket.socket, sender: str) -> None:
        """Receive a file from a client.

        Protocol:
            1. Receive 4-byte header length
            2. Receive JSON header: {filename, file_size}
            3. Receive file data in chunks
        """
        try:
            client_socket.settimeout(30.0)

            # Read header length (4 bytes, big-endian)
            header_len_data = self._recv_exact(client_socket, 4)
            if not header_len_data:
                return
            header_len = struct.unpack('>I', header_len_data)[0]

            # Read header
            header_data = self._recv_exact(client_socket, header_len)
            if not header_data:
                return
            header = json.loads(header_data.decode('utf-8'))

            filename = os.path.basename(header['filename'])
            file_size = header['file_size']

            self.transfer_started.emit(filename, file_size, sender)
            logger.info("Receiving file: %s (%d bytes) from %s",
                         filename, file_size, sender)

            # Ensure save directory exists
            os.makedirs(self._save_dir, exist_ok=True)
            save_path = os.path.join(self._save_dir, filename)

            # Avoid overwriting
            base, ext = os.path.splitext(save_path)
            counter = 1
            while os.path.exists(save_path):
                save_path = f"{base}_{counter}{ext}"
                counter += 1

            # Receive file data
            bytes_received = 0
            with open(save_path, 'wb') as f:
                while bytes_received < file_size:
                    remaining = file_size - bytes_received
                    chunk_size = min(self._chunk_size, remaining)
                    data = client_socket.recv(chunk_size)
                    if not data:
                        raise ConnectionError("Connection lost during transfer")
                    f.write(data)
                    bytes_received += len(data)
                    self.transfer_progress.emit(bytes_received, file_size)

            # Send acknowledgment
            client_socket.sendall(b"OK")

            self.transfer_complete.emit(filename, save_path)
            logger.info("File received: %s -> %s", filename, save_path)

        except Exception as e:
            self.transfer_error.emit(f"File receive error: {str(e)}")
            logger.error("File receive error: %s", e)
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> Optional[bytes]:
        """Receive exactly size bytes from socket."""
        data = bytearray()
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data)


# ─── File Transfer Client ────────────────────────────────────────────

class FileTransferClient(QThread):
    """Client for sending files over TCP.

    Signals:
        transfer_started: (filename: str, file_size: int)
        transfer_progress: (bytes_sent: int, total: int)
        transfer_complete: (filename: str)
        transfer_error: (error_message: str)
        speed_update: (bytes_per_sec: float)
    """

    transfer_started = Signal(str, int)
    transfer_progress = Signal(int, int)
    transfer_complete = Signal(str)
    transfer_error = Signal(str)
    speed_update = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_ip: str = ""
        self._target_port: int = 5003
        self._file_path: str = ""
        self._chunk_size: int = 8192
        self._cancelled: bool = False

    def configure(self, target_ip: str, target_port: int,
                  file_path: str, chunk_size: int = 8192) -> None:
        """Configure file transfer."""
        self._target_ip = target_ip
        self._target_port = target_port
        self._file_path = file_path
        self._chunk_size = chunk_size
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the transfer."""
        self._cancelled = True

    def run(self) -> None:
        """Send the file."""
        sock = None
        try:
            if not os.path.isfile(self._file_path):
                self.transfer_error.emit(f"File not found: {self._file_path}")
                return

            filename = os.path.basename(self._file_path)
            file_size = os.path.getsize(self._file_path)

            # Connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((self._target_ip, self._target_port))

            # Send header
            header = json.dumps({
                'filename': filename,
                'file_size': file_size,
            }).encode('utf-8')
            sock.sendall(struct.pack('>I', len(header)))
            sock.sendall(header)

            self.transfer_started.emit(filename, file_size)
            logger.info("Sending file: %s (%d bytes) to %s:%d",
                         filename, file_size, self._target_ip, self._target_port)

            # Send file data
            bytes_sent = 0
            start_time = time.time()
            last_speed_update = start_time

            with open(self._file_path, 'rb') as f:
                while bytes_sent < file_size:
                    if self._cancelled:
                        self.transfer_error.emit("Transfer cancelled")
                        return

                    data = f.read(self._chunk_size)
                    if not data:
                        break
                    sock.sendall(data)
                    bytes_sent += len(data)
                    self.transfer_progress.emit(bytes_sent, file_size)

                    # Speed update every 0.5s
                    now = time.time()
                    if now - last_speed_update >= 0.5:
                        elapsed = now - start_time
                        if elapsed > 0:
                            speed = bytes_sent / elapsed
                            self.speed_update.emit(speed)
                        last_speed_update = now

            # Wait for acknowledgment
            sock.settimeout(10.0)
            ack = sock.recv(16)

            self.transfer_complete.emit(filename)
            logger.info("File sent successfully: %s", filename)

        except ConnectionRefusedError:
            self.transfer_error.emit(
                f"Connection refused: {self._target_ip}:{self._target_port}"
            )
        except socket.timeout:
            self.transfer_error.emit("Transfer timed out")
        except Exception as e:
            self.transfer_error.emit(f"Transfer error: {str(e)}")
            logger.error("File transfer error: %s", e)
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass


# ─── LAN Chat ────────────────────────────────────────────────────────

class LANChatServer(QThread):
    """TCP-based chat server for LAN messaging.

    Signals:
        chat_message: (username: str, message: str, ip: str, timestamp: str)
        user_joined: (username: str, ip: str)
        user_left: (username: str, ip: str)
        server_started: (port: int)
        server_stopped: ()
        chat_error: (error: str)
    """

    chat_message = Signal(str, str, str, str)
    user_joined = Signal(str, str)
    user_left = Signal(str, str)
    server_started = Signal(int)
    server_stopped = Signal()
    chat_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port: int = 5002
        self._running: bool = False
        self._server_socket: Optional[socket.socket] = None
        self._clients: Dict[str, dict] = {}  # addr -> {socket, username}
        self._clients_lock = threading.Lock()

    def configure(self, port: int = 5002) -> None:
        """Configure chat server."""
        self._port = port

    def stop(self) -> None:
        """Stop the chat server."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def broadcast_message(self, username: str, message: str,
                          exclude: Optional[str] = None) -> None:
        """Broadcast a chat message to all connected clients."""
        msg_data = json.dumps({
            'type': 'message',
            'username': username,
            'message': message,
            'timestamp': time.strftime("%H:%M:%S"),
        }).encode('utf-8')

        with self._clients_lock:
            clients_snapshot = list(self._clients.items())
        for addr, info in clients_snapshot:
            if addr != exclude:
                try:
                    info['socket'].sendall(msg_data + b'\n')
                except (OSError, BrokenPipeError):
                    self._remove_client(addr)

    def run(self) -> None:
        """Chat server main loop."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.settimeout(1.0)
            self._server_socket.bind(("0.0.0.0", self._port))
            self._server_socket.listen(20)
            self._running = True

            self.server_started.emit(self._port)
            logger.info("LAN Chat server started on port %d", self._port)

            with ThreadPoolExecutor(max_workers=20) as executor:
                while self._running:
                    try:
                        client_socket, addr = self._server_socket.accept()
                        client_addr = f"{addr[0]}:{addr[1]}"
                        with self._clients_lock:
                            self._clients[client_addr] = {
                                'socket': client_socket,
                                'username': 'Unknown',
                                'ip': addr[0],
                            }
                        executor.submit(self._handle_chat_client,
                                        client_socket, client_addr, addr[0])
                    except socket.timeout:
                        continue
                    except OSError:
                        if self._running:
                            break
        except OSError as e:
            self.chat_error.emit(f"Chat server error: {str(e)}")
        finally:
            self._cleanup()

    def _handle_chat_client(self, sock: socket.socket,
                            addr: str, ip: str) -> None:
        """Handle a chat client."""
        buffer = ""
        try:
            sock.settimeout(None)
            while self._running:
                with self._clients_lock:
                    if addr not in self._clients:
                        break
                try:
                    data = sock.recv(4096)
                    if not data:
                        break

                    buffer += data.decode('utf-8', errors='replace')

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            msg = json.loads(line)
                            msg_type = msg.get('type', '')

                            if msg_type == 'join':
                                username = msg.get('username', 'Unknown')
                                with self._clients_lock:
                                    if addr in self._clients:
                                        self._clients[addr]['username'] = username
                                self.user_joined.emit(username, ip)
                                # Notify others
                                self.broadcast_message(
                                    "System",
                                    f"{username} has joined the chat",
                                    exclude=addr
                                )

                            elif msg_type == 'message':
                                with self._clients_lock:
                                    username = self._clients.get(
                                        addr, {}
                                    ).get('username', 'Unknown')
                                message = msg.get('message', '')
                                timestamp = msg.get(
                                    'timestamp',
                                    time.strftime("%H:%M:%S")
                                )
                                self.chat_message.emit(
                                    username, message, ip, timestamp
                                )
                                self.broadcast_message(
                                    username, message, exclude=addr
                                )

                        except json.JSONDecodeError:
                            continue

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except OSError:
                    break
        finally:
            self._remove_client(addr)

    def _remove_client(self, addr: str) -> None:
        """Remove a chat client."""
        with self._clients_lock:
            client_info = self._clients.pop(addr, None)
        if client_info:
            username = client_info.get('username', 'Unknown')
            ip = client_info.get('ip', '')
            try:
                client_info['socket'].close()
            except OSError:
                pass
            self.user_left.emit(username, ip)
            self.broadcast_message("System", f"{username} has left the chat")

    def _cleanup(self) -> None:
        """Clean up all resources."""
        self._running = False
        with self._clients_lock:
            addrs = list(self._clients.keys())
        for addr in addrs:
            self._remove_client(addr)
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        self.server_stopped.emit()


class LANChatClient(QThread):
    """TCP-based chat client.

    Signals:
        connected: ()
        disconnected: ()
        chat_message: (username: str, message: str, timestamp: str)
        chat_error: (error: str)
    """

    connected = Signal()
    disconnected = Signal()
    chat_message = Signal(str, str, str)
    chat_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._host: str = ""
        self._port: int = 5002
        self._username: str = ""
        self._socket: Optional[socket.socket] = None
        self._running: bool = False

    def configure(self, host: str, port: int, username: str) -> None:
        """Configure chat client."""
        self._host = host
        self._port = port
        self._username = username

    @property
    def is_connected(self) -> bool:
        return self._running

    def disconnect_chat(self) -> None:
        """Disconnect from chat server."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def send_chat_message(self, message: str) -> bool:
        """Send a chat message."""
        if not self._socket or not self._running:
            return False
        try:
            msg_data = json.dumps({
                'type': 'message',
                'username': self._username,
                'message': message,
                'timestamp': time.strftime("%H:%M:%S"),
            }).encode('utf-8')
            self._socket.sendall(msg_data + b'\n')
            return True
        except (OSError, BrokenPipeError) as e:
            self.chat_error.emit(f"Send error: {str(e)}")
            self.disconnect_chat()
            return False

    def run(self) -> None:
        """Connect and listen for messages."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self._host, self._port))
            self._running = True
            self._socket.settimeout(1.0)

            # Send join message
            join_msg = json.dumps({
                'type': 'join',
                'username': self._username,
            }).encode('utf-8')
            self._socket.sendall(join_msg + b'\n')

            self.connected.emit()
            logger.info("Chat connected to %s:%d as %s",
                         self._host, self._port, self._username)

            buffer = ""
            while self._running:
                try:
                    data = self._socket.recv(4096)
                    if not data:
                        break

                    buffer += data.decode('utf-8', errors='replace')

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line)
                            if msg.get('type') == 'message':
                                self.chat_message.emit(
                                    msg.get('username', 'Unknown'),
                                    msg.get('message', ''),
                                    msg.get('timestamp', ''),
                                )
                        except json.JSONDecodeError:
                            continue

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except OSError:
                    if self._running:
                        break

        except ConnectionRefusedError:
            self.chat_error.emit(f"Chat server not available at {self._host}:{self._port}")
        except socket.timeout:
            self.chat_error.emit("Connection timed out")
        except OSError as e:
            self.chat_error.emit(f"Chat error: {str(e)}")
        finally:
            self._running = False
            if self._socket:
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None
            self.disconnected.emit()
