"""Test the CodeEditor class."""
from PySide2.QtNetwork import QTcpServer, QTcpSocket
from PySide2.QtWebSockets import QWebSocket, QWebSocketServer

from src.settings import AppSettings
from src.network.nss_client import QBaseClient
from src.network.nss_server import QServer
from src.network.nss_socket import _TcpSocket, _WebSocket


def test_server_is_websocket_server():
    """If websocket settings is true, server should be a webserversocket."""
    AppSettings().setValue('connection_type/websocket', True)
    server = QServer().server
    assert isinstance(server, QWebSocketServer)


def test_server_is_tcp_server():
    """If websocket settings is false, server should be a tcpserver."""
    server = QServer().server
    assert isinstance(server, QTcpServer)


def test_test_client_is_websocket():
    """If websocket settings is true, client should be a websocket."""
    AppSettings().setValue('connection_type/websocket', True)
    socket = QBaseClient('localhost', 54321).socket._socket
    assert isinstance(socket, QWebSocket)


def test_test_client_is_tcpsocket():
    """If websocket settings is false, socket should be a tcpsocket."""
    AppSettings().setValue('connection_type/tcp', True)
    socket = QBaseClient('localhost', 54321).socket._socket
    assert isinstance(socket, QTcpSocket)


def test_abstract_tcp_socket():
    """Test if abstract socket class is _TcpSocket."""
    AppSettings().setValue('connection_type/tcp', True)
    socket = QBaseClient('localhost', 54321).socket
    assert isinstance(socket, _TcpSocket)


def test_abstract_websocket():
    """Test if abstract socket class is _WebSocket."""
    AppSettings().setValue('connection_type/websocket', True)
    socket = QBaseClient('localhost', 54321).socket
    assert isinstance(socket, _WebSocket)
