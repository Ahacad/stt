"""Test socket client against mock server."""

import os
import socket
import tempfile
import threading

from stt.client import daemon_running, daemon_send


def test_daemon_running_false_no_socket(tmp_path):
    """daemon_running returns False when there's no socket."""
    import stt.client as client_mod

    original = client_mod.SOCKET_PATH
    try:
        client_mod.SOCKET_PATH = str(tmp_path / "nonexistent.sock")
        assert not daemon_running()
    finally:
        client_mod.SOCKET_PATH = original


def test_daemon_running_true(tmp_path):
    """daemon_running returns True against a mock pong server."""
    sock_path = str(tmp_path / "test.sock")

    def serve():
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(sock_path)
        srv.listen(1)
        conn, _ = srv.accept()
        data = conn.recv(64)
        if data == b"ping":
            conn.sendall(b"pong")
        conn.close()
        srv.close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    # Wait for server to be ready
    import time
    for _ in range(50):
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)

    import stt.config as cfg
    original = cfg.SOCKET_PATH
    try:
        cfg.SOCKET_PATH = sock_path
        # Patch the module-level import in client
        import stt.client as client_mod
        client_mod.SOCKET_PATH = sock_path
        assert daemon_running()
    finally:
        cfg.SOCKET_PATH = original
        client_mod.SOCKET_PATH = original

    t.join(timeout=2)


def test_daemon_send(tmp_path):
    """daemon_send sends command and receives response."""
    sock_path = str(tmp_path / "test.sock")

    def serve():
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(sock_path)
        srv.listen(1)
        conn, _ = srv.accept()
        data = conn.recv(4096).decode()
        conn.sendall(f"echo:{data}".encode())
        conn.close()
        srv.close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    import time
    for _ in range(50):
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)

    import stt.client as client_mod
    original = client_mod.SOCKET_PATH
    try:
        client_mod.SOCKET_PATH = sock_path
        result = daemon_send("hello world")
        assert result == "echo:hello world"
    finally:
        client_mod.SOCKET_PATH = original

    t.join(timeout=2)
