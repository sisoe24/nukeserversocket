# get current ip

import socket


def get_ip():
    """Return the local network ip address.

    Get ip network with python socket modules. If socket error happens, then
    will return the local host `127.0.0.1`.

    Returns:
        str: network ip address (eg. 192.168.1.60)
    """
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _socket.connect(('10.255.255.255', 1))
        ip, _ = _socket.getsockname()
    except socket.error:
        ip = '127.0.0.1'
    finally:
        _socket.close()
    return ip
