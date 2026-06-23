# network.py
import socket
import json
import time

def send_data(sock, data):
    try:
        message = json.dumps(data) + '\n'
        sock.send(message.encode('utf-8'))
        return True
    except Exception as e:
        print(f"⚠️ Send error: {e}")
        return False

def recv_data(sock, timeout=0.1):
    buffer = ''
    sock.settimeout(timeout)
    try:
        while True:
            chunk = sock.recv(4096).decode('utf-8')
            if not chunk:
                return None
            buffer += chunk
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    except socket.timeout:
        return None
    except Exception as e:
        print(f"⚠️ Receive error: {e}")
        return None
    finally:
        sock.settimeout(None)