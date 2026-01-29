import socket
import threading
import json
import traceback
import sys
import re
from collections import defaultdict

class PortForwardServer:
    def __init__(self, InternalDataPort=5000, AllowedPortRange="5001-5500", MaxPortsPerClient=5, Key="07A36AEF1907843"):
        self.InternalDataPort = InternalDataPort
        self.AllowedPortRange = AllowedPortRange
        self.MaxPortsPerClient = MaxPortsPerClient
        self.Key = Key
        self.ParsePortRange()
        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Clients = {}
        self.ClientLocks = defaultdict(threading.Lock)
        self.ForwardMap = {}
        self.ForwardLocks = defaultdict(threading.Lock)
        self.Running = True
        self.MessageSeparator = b'|||'

    def ParsePortRange(self):
        match = re.match(r'^(\d+)-(\d+)$', self.AllowedPortRange)
        if not match:
            raise ValueError("Invalid port range format")
        self.MinPort = int(match.group(1))
        self.MaxPort = int(match.group(2))
        if self.MinPort >= self.MaxPort or self.MinPort < 1 or self.MaxPort > 65535:
            raise ValueError("Invalid port range values")

    def IsPortAllowed(self, port):
        return self.MinPort <= port <= self.MaxPort

    def Start(self):
        try:
            self.ServerSocket.bind(('0.0.0.0', self.InternalDataPort))
            self.ServerSocket.listen(5)
            print(f"Server started on port {self.InternalDataPort}")
            acceptThread = threading.Thread(target=self.AcceptClients, daemon=True)
            acceptThread.start()
            while self.Running:
                cmd = input("Enter 'exit' to stop server: ")
                if cmd.lower() == 'exit':
                    self.Running = False
                    break
            self.Stop()
        except Exception as e:
            print(f"Server start error: {e}")
            traceback.print_exc()

    def Stop(self):
        self.Running = False
        self.ServerSocket.close()
        for clientId, clientData in self.Clients.items():
            with self.ClientLocks[clientId]:
                if clientData['socket']:
                    try:
                        clientData['socket'].close()
                    except:
                        pass
            with self.ForwardLocks[clientId]:
                for forwardId, forwardData in clientData['forwards'].items():
                    try:
                        forwardData['server'].close()
                    except:
                        pass
        print("Server stopped")

    def AcceptClients(self):
        while self.Running:
            try:
                clientSocket, addr = self.ServerSocket.accept()
                print(f"New client connection from {addr}")
                clientThread = threading.Thread(target=self.HandleClient, args=(clientSocket, addr), daemon=True)
                clientThread.start()
            except Exception as e:
                if self.Running:
                    print(f"Accept error: {e}")
                    traceback.print_exc()

    def HandleClient(self, clientSocket, addr):
        clientId = f"{addr[0]}:{addr[1]}"
        self.Clients[clientId] = {'socket': clientSocket, 'forwards': {}, 'addr': addr, 'buffer': b''}
        try:
            while self.Running:
                clientSocket.settimeout(30)
                try:
                    data = clientSocket.recv(4096)
                    if not data:
                        print(f"Client {clientId} disconnected")
                        break
                    self.Clients[clientId]['buffer'] += data
                    self.ProcessBuffer(clientId)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Client communication error: {e}")
                    traceback.print_exc()
                    break
        finally:
            with self.ClientLocks[clientId]:
                if clientId in self.Clients:
                    del self.Clients[clientId]
            with self.ForwardLocks[clientId]:
                for forwardId in list(self.ForwardMap.keys()):
                    if forwardId.startswith(clientId):
                        del self.ForwardMap[forwardId]
            try:
                clientSocket.close()
            except:
                pass
            print(f"Client {clientId} handler cleaned up")

    def ProcessBuffer(self, clientId):
        clientData = self.Clients.get(clientId)
        if not clientData:
            return
        while self.MessageSeparator in clientData['buffer']:
            msgEnd = clientData['buffer'].index(self.MessageSeparator)
            messageData = clientData['buffer'][:msgEnd]
            clientData['buffer'] = clientData['buffer'][msgEnd + len(self.MessageSeparator):]
            try:
                message = json.loads(messageData.decode('utf-8'))
                self.ProcessClientMessage(clientId, message)
            except json.JSONDecodeError:
                print(f"Invalid JSON from client {clientId}")
                self.SendToClient(clientId, {'type': 'error', 'message': 'Invalid JSON'})
            except Exception as e:
                print(f"Error processing message: {e}")
                traceback.print_exc()

    def ProcessClientMessage(self, clientId, message):
        if message.get('type') == 'auth':
            self.HandleAuth(clientId, message)
        elif message.get('type') == 'forward_request':
            self.HandleForwardRequest(clientId, message)
        elif message.get('type') == 'data':
            self.HandleData(clientId, message)
        elif message.get('type') == 'close_forward':
            self.HandleCloseForward(clientId, message)
        else:
            self.SendToClient(clientId, {'type': 'error', 'message': 'Unknown message type'})

    def HandleAuth(self, clientId, message):
        clientData = self.Clients.get(clientId)
        if not clientData:
            return
        if message.get('key') == self.Key:
            clientData['authenticated'] = True
            self.SendToClient(clientId, {'type': 'auth_response', 'success': True})
            print(f"Client {clientId} authenticated successfully")
        else:
            self.SendToClient(clientId, {'type': 'auth_response', 'success': False, 'message': 'Invalid key'})
            clientData['socket'].close()
            print(f"Client {clientId} failed authentication")

    def HandleForwardRequest(self, clientId, message):
        clientData = self.Clients.get(clientId)
        if not clientData or not clientData.get('authenticated', False):
            self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': 'Not authenticated'})
            return
        with self.ClientLocks[clientId]:
            if len(clientData['forwards']) >= self.MaxPortsPerClient:
                self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': 'Max ports per client reached'})
                return
        targetPort = message.get('target_port')
        mode = message.get('mode', 'tcp').upper()
        if not self.IsPortAllowed(targetPort):
            self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': 'Target port not allowed'})
            return
        forwardId = f"{clientId}:{targetPort}"
        if forwardId in self.ForwardMap:
            self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': 'Port already in use'})
            return
        try:
            if mode == 'TCP':
                forwardServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                forwardServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                forwardServer.bind(('0.0.0.0', targetPort))
                forwardServer.listen(5)
                with self.ClientLocks[clientId]:
                    clientData['forwards'][forwardId] = {'server': forwardServer, 'mode': mode, 'connections': {}}
                with self.ForwardLocks[clientId]:
                    self.ForwardMap[forwardId] = clientId
                threading.Thread(target=self.AcceptForwardConnections, args=(clientId, forwardId, forwardServer), daemon=True).start()
                self.SendToClient(clientId, {'type': 'forward_response', 'success': True, 'target_port': targetPort, 'forward_id': forwardId})
                print(f"Forward created: {forwardId}")
            else:
                self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': 'Unsupported mode'})
        except Exception as e:
            print(f"Forward creation error: {e}")
            traceback.print_exc()
            self.SendToClient(clientId, {'type': 'forward_response', 'success': False, 'message': str(e)})

    def AcceptForwardConnections(self, clientId, forwardId, forwardServer):
        try:
            while self.Running and forwardId in self.ForwardMap and self.ForwardMap[forwardId] == clientId:
                forwardServer.settimeout(1)
                try:
                    conn, addr = forwardServer.accept()
                    connId = f"{addr[0]}:{addr[1]}"
                    print(f"New connection to forward {forwardId} from {connId}")
                    with self.ClientLocks[clientId]:
                        clientData = self.Clients.get(clientId)
                        if not clientData or forwardId not in clientData['forwards']:
                            conn.close()
                            continue
                        clientData['forwards'][forwardId]['connections'][connId] = conn
                    self.SendToClient(clientId, {
                        'type': 'new_connection',
                        'forward_id': forwardId,
                        'conn_id': connId
                    })
                    threading.Thread(target=self.ForwardToClient, args=(clientId, forwardId, connId, conn), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Forward accept error: {e}")
                    traceback.print_exc()
        finally:
            try:
                forwardServer.close()
            except:
                pass
            print(f"Forward listener {forwardId} stopped")

    def ForwardToClient(self, clientId, forwardId, connId, conn):
        try:
            while self.Running:
                conn.settimeout(1)
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    self.SendToClient(clientId, {
                        'type': 'data',
                        'forward_id': forwardId,
                        'conn_id': connId,
                        'data': data.hex()
                    })
                except socket.timeout:
                    if not self.Running or clientId not in self.Clients:
                        break
                    continue
                except Exception as e:
                    print(f"Forward to client error: {e}")
                    traceback.print_exc()
                    break
        finally:
            try:
                conn.close()
            except:
                pass
            with self.ClientLocks[clientId]:
                clientData = self.Clients.get(clientId)
                if clientData and forwardId in clientData['forwards']:
                    if connId in clientData['forwards'][forwardId]['connections']:
                        del clientData['forwards'][forwardId]['connections'][connId]
            self.SendToClient(clientId, {
                'type': 'close_connection',
                'forward_id': forwardId,
                'conn_id': connId
            })
            print(f"Connection {connId} to forward {forwardId} closed")

    def HandleData(self, clientId, message):
        forwardId = message.get('forward_id')
        connId = message.get('conn_id')
        dataHex = message.get('data')
        if not all([forwardId, connId, dataHex]):
            return
        try:
            data = bytes.fromhex(dataHex)
            with self.ClientLocks[clientId]:
                clientData = self.Clients.get(clientId)
                if not clientData or forwardId not in clientData['forwards']:
                    return
                forwardData = clientData['forwards'][forwardId]
                if connId not in forwardData['connections']:
                    return
                conn = forwardData['connections'][connId]
                conn.sendall(data)
        except Exception as e:
            print(f"Data handling error: {e}")
            traceback.print_exc()

    def HandleCloseForward(self, clientId, message):
        forwardId = message.get('forward_id')
        if not forwardId:
            return
        with self.ClientLocks[clientId]:
            clientData = self.Clients.get(clientId)
            if clientData and forwardId in clientData['forwards']:
                try:
                    clientData['forwards'][forwardId]['server'].close()
                except:
                    pass
                del clientData['forwards'][forwardId]
        with self.ForwardLocks[clientId]:
            if forwardId in self.ForwardMap:
                del self.ForwardMap[forwardId]
        print(f"Forward {forwardId} closed by client")

    def SendToClient(self, clientId, message):
        try:
            with self.ClientLocks[clientId]:
                clientData = self.Clients.get(clientId)
                if not clientData or not clientData['socket']:
                    return
                clientSocket = clientData['socket']
                data = json.dumps(message).encode('utf-8') + self.MessageSeparator
                clientSocket.sendall(data)
        except Exception as e:
            print(f"Error sending to client {clientId}: {e}")
            traceback.print_exc()

def main():
    config = {
        "InternalDataPort": 5000,
        "AllowedPortRange": "5001-5500",
        "MaxPortsPerClient": 5,
        "Key": "07A36AEF1907843"
    }
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config file: {e}")
            traceback.print_exc()
    server = PortForwardServer(
        InternalDataPort=int(config["InternalDataPort"]),
        AllowedPortRange=config["AllowedPortRange"],
        MaxPortsPerClient=int(config["MaxPortsPerClient"]),
        Key=config["Key"]
    )
    server.Start()

if __name__ == "__main__":
    main()
