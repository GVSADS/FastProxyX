import socket
import threading
import json
import traceback
import sys
import time

class PortForwardClient:
    def __init__(self, ServerDomain="127.0.0.1", ServerPort=5000, Forwards=None, Key="07A36AEF1907843"):
        self.ServerDomain = ServerDomain
        self.ServerPort = ServerPort
        self.Forwards = Forwards or []
        self.Key = Key
        self.ServerSocket = None
        self.Running = True
        self.ForwardMap = {}
        self.ConnectionMap = {}
        self.Lock = threading.Lock()
        self.Buffer = b''
        self.MessageSeparator = b'|||'

    def Start(self):
        try:
            self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ServerSocket.connect((self.ServerDomain, self.ServerPort))
            print(f"Connected to server {self.ServerDomain}:{self.ServerPort}")
            self.Authenticate()
            threading.Thread(target=self.ReceiveFromServer, daemon=True).start()
            self.SetupForwards()
            while self.Running:
                time.sleep(5)
        except Exception as e:
            print(f"Client start error: {e}")
            traceback.print_exc()
            self.Stop()

    def Stop(self):
        self.Running = False
        with self.Lock:
            for forwardId, forwardData in self.ForwardMap.items():
                try:
                    self.SendToServer({'type': 'close_forward', 'forward_id': forwardId})
                except:
                    pass
                for connId, conn in forwardData['connections'].items():
                    try:
                        conn.close()
                    except:
                        pass
            self.ForwardMap.clear()
            self.ConnectionMap.clear()
        if self.ServerSocket:
            try:
                self.ServerSocket.close()
            except:
                pass
        print("Client stopped")

    def Authenticate(self):
        self.SendToServer({'type': 'auth', 'key': self.Key})
        response = self.ServerSocket.recv(4096)
        if not response:
            raise ConnectionError("Server closed connection during authentication")
        self.Buffer += response
        self.ProcessBuffer()

    def SetupForwards(self):
        for forward in self.Forwards:
            forwardDomain = forward.get('forward_domain', '127.0.0.1')
            forwardPort = forward.get('forward_port')
            targetPort = forward.get('target_port')
            mode = forward.get('mode', 'tcp').upper()
            if not all([forwardPort, targetPort]):
                print("Invalid forward configuration, skipping")
                continue
            self.SendToServer({
                'type': 'forward_request',
                'forward_domain': forwardDomain,
                'forward_port': forwardPort,
                'target_port': targetPort,
                'mode': mode
            })

    def ReceiveFromServer(self):
        while self.Running and self.ServerSocket:
            try:
                self.ServerSocket.settimeout(1)
                data = self.ServerSocket.recv(4096)
                if not data:
                    print("Server disconnected")
                    self.Running = False
                    break
                self.Buffer += data
                self.ProcessBuffer()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Server communication error: {e}")
                traceback.print_exc()
                self.Running = False
                break

    def ProcessBuffer(self):
        while self.MessageSeparator in self.Buffer:
            msgEnd = self.Buffer.index(self.MessageSeparator)
            messageData = self.Buffer[:msgEnd]
            self.Buffer = self.Buffer[msgEnd + len(self.MessageSeparator):]
            try:
                message = json.loads(messageData.decode('utf-8'))
                self.ProcessServerMessage(message)
            except json.JSONDecodeError:
                print("Received invalid JSON from server")
            except Exception as e:
                print(f"Error processing server data: {e}")
                traceback.print_exc()

    def ProcessServerMessage(self, message):
        if message.get('type') == 'forward_response':
            self.HandleForwardResponse(message)
        elif message.get('type') == 'new_connection':
            self.HandleNewConnection(message)
        elif message.get('type') == 'data':
            self.HandleData(message)
        elif message.get('type') == 'close_connection':
            self.HandleCloseConnection(message)
        elif message.get('type') == 'error':
            print(f"Server error: {message.get('message')}")

    def HandleForwardResponse(self, message):
        if message.get('success'):
            forwardId = message.get('forward_id')
            targetPort = message.get('target_port')
            forwardConfig = next((f for f in self.Forwards if f.get('target_port') == targetPort), None)
            if forwardConfig and forwardId:
                with self.Lock:
                    self.ForwardMap[forwardId] = {
                        'config': forwardConfig,
                        'connections': {}
                    }
                print(f"Forward established: {forwardId}")
            else:
                print(f"Received forward response for unknown target port {targetPort}")
        else:
            print(f"Forward request failed: {message.get('message')}")

    def HandleNewConnection(self, message):
        forwardId = message.get('forward_id')
        connId = message.get('conn_id')
        if not all([forwardId, connId]):
            return
        with self.Lock:
            if forwardId not in self.ForwardMap:
                print(f"Received connection for unknown forward {forwardId}")
                return
            forwardData = self.ForwardMap[forwardId]
            config = forwardData['config']
        try:
            if config.get('mode', 'tcp').upper() == 'TCP':
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((config['forward_domain'], config['forward_port']))
                with self.Lock:
                    forwardData['connections'][connId] = conn
                    self.ConnectionMap[connId] = forwardId
                threading.Thread(target=self.ForwardToServer, args=(forwardId, connId, conn), daemon=True).start()
                print(f"Established connection {connId} for forward {forwardId}")
            else:
                print(f"Unsupported mode for forward {forwardId}")
        except Exception as e:
            print(f"Error establishing connection for {forwardId}: {e}")
            traceback.print_exc()
            self.SendToServer({
                'type': 'close_connection',
                'forward_id': forwardId,
                'conn_id': connId
            })

    def ForwardToServer(self, forwardId, connId, conn):
        try:
            while self.Running:
                conn.settimeout(1)
                try:
                    with self.Lock:
                        if connId not in self.ConnectionMap or self.ConnectionMap[connId] != forwardId:
                            break
                    data = conn.recv(4096)
                    if not data:
                        break
                    self.SendToServer({
                        'type': 'data',
                        'forward_id': forwardId,
                        'conn_id': connId,
                        'data': data.hex()
                    })
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Forward to server error: {e}")
                    traceback.print_exc()
                    break
        finally:
            try:
                conn.close()
            except:
                pass
            with self.Lock:
                if forwardId in self.ForwardMap and connId in self.ForwardMap[forwardId]['connections']:
                    del self.ForwardMap[forwardId]['connections'][connId]
                if connId in self.ConnectionMap:
                    del self.ConnectionMap[connId]
            self.SendToServer({
                'type': 'close_connection',
                'forward_id': forwardId,
                'conn_id': connId
            })
            print(f"Closed connection {connId} for forward {forwardId}")

    def HandleData(self, message):
        forwardId = message.get('forward_id')
        connId = message.get('conn_id')
        dataHex = message.get('data')
        if not all([forwardId, connId, dataHex]):
            return
        try:
            data = bytes.fromhex(dataHex)
            with self.Lock:
                if forwardId not in self.ForwardMap or connId not in self.ForwardMap[forwardId]['connections']:
                    print(f"Received data for unknown connection {connId}")
                    return
                conn = self.ForwardMap[forwardId]['connections'][connId]
            conn.sendall(data)
        except Exception as e:
            print(f"Data handling error: {e}")
            traceback.print_exc()
            self.SendToServer({
                'type': 'close_connection',
                'forward_id': forwardId,
                'conn_id': connId
            })

    def HandleCloseConnection(self, message):
        forwardId = message.get('forward_id')
        connId = message.get('conn_id')
        with self.Lock:
            if forwardId in self.ForwardMap and connId in self.ForwardMap[forwardId]['connections']:
                try:
                    self.ForwardMap[forwardId]['connections'][connId].close()
                except:
                    pass
                del self.ForwardMap[forwardId]['connections'][connId]
            if connId in self.ConnectionMap:
                del self.ConnectionMap[connId]
        print(f"Connection {connId} for forward {forwardId} closed by server")

    def SendToServer(self, message):
        if not self.ServerSocket or not self.Running:
            return
        try:
            data = json.dumps(message).encode('utf-8') + self.MessageSeparator
            self.ServerSocket.sendall(data)
        except Exception as e:
            print(f"Error sending to server: {e}")
            traceback.print_exc()
            self.Running = False

def main():
    config = {
        "ServerDomain": "127.0.0.1",
        "ServerPort": 5000,
        "Key": "07A36AEF1907843",
        "Forwards": [
            {
                "forward_domain": "127.0.0.1",
                "forward_port": 36667,
                "target_port": 5002,
                "mode": "TCP"
            }
        ]
    }
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config file: {e}")
            traceback.print_exc()
    client = PortForwardClient(
        ServerDomain=config["ServerDomain"],
        ServerPort=int(config["ServerPort"]),
        Forwards=config["Forwards"],
        Key=config["Key"]
    )
    client.Start()

if __name__ == "__main__":
    main()
