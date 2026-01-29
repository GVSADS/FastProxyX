# -*- coding: utf-8 -*-
# Brief Introduction
# The original Frp (https://github.com/Fatedier/frp/) is somewhat bloated in size,
# while PyFrp is a simplified Python-based implementation with a smaller footprint and fewer features.

import socket
import threading
import json
import traceback
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import re
import sys
import os

class AesEncryptor:
    def __init__(self, Key):
        self.Key = Key.ljust(32)[:32].encode('utf-8')
        self.Mode = AES.MODE_CBC
    def Encrypt(self, Data):
        Iv = b'0123456789abcdef'
        Cipher = AES.new(self.Key, self.Mode, Iv)
        return base64.b64encode(Iv + Cipher.encrypt(pad(Data.encode('utf-8'), AES.block_size))).decode('utf-8')
    def Decrypt(self, Data):
        Data = base64.b64decode(Data)
        Iv = Data[:16]
        Cipher = AES.new(self.Key, self.Mode, Iv)
        return unpad(Cipher.decrypt(Data[16:]), AES.block_size).decode('utf-8')

class PortRange:
    def __init__(self, RangeStr):
        Match = re.match(r'^(\d+)-(\d+)$', RangeStr)
        if not Match:
            raise ValueError("Invalid port range format")
        self.Start = int(Match.group(1))
        self.End = int(Match.group(2))
        if self.Start < 1 or self.End > 65535 or self.Start > self.End:
            raise ValueError("Invalid port range values")
    def IsInRange(self, Port):
        return self.Start <= Port <= self.End

class ClientHandler:
    def __init__(self, Server, ClientSocket, Address):
        self.Server = Server
        self.ClientSocket = ClientSocket
        self.Address = Address
        self.IsRunning = True
        self.Mappings = {}
        self.Encryptor = AesEncryptor(Server.Key)
        self.Log("New client connected")
    def Log(self, Message):
        Timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{Timestamp}] [Client {self.Address}] {Message}")
    def HandleError(self, Message):
        self.Log(f"Error: {Message}")
        self.Log(traceback.format_exc())
    def Close(self):
        self.IsRunning = False
        for Mapping in self.Mappings.values():
            Mapping.Close()
        self.Mappings.clear()
        try:
            self.ClientSocket.close()
        except:
            pass
        self.Log("Client disconnected")
    def CreateTcpMapping(self, ForwardHost, ForwardPort, TargetPort):
        try:
            ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ServerSocket.bind(('0.0.0.0', TargetPort))
            ServerSocket.listen(5)
            Mapping = TcpMapping(self, ServerSocket, ForwardHost, ForwardPort, TargetPort)
            self.Mappings[TargetPort] = Mapping
            threading.Thread(target=Mapping.Start, daemon=True).start()
            return True
        except Exception as E:
            self.HandleError(f"Failed to create TCP mapping: {str(E)}")
            return False
    def RemoveMapping(self, TargetPort):
        if TargetPort in self.Mappings:
            self.Mappings[TargetPort].Close()
            del self.Mappings[TargetPort]
            return True
        return False
    def ProcessCommand(self, Command):
        try:
            CmdType = Command.get('type')
            if CmdType == 'register':
                if len(self.Mappings) >= self.Server.MaxPortsPerClient:
                    return {'status': 'error', 'message': f'Max {self.Server.MaxPortsPerClient} ports per client'}
                TargetPort = Command.get('target_port')
                if not self.Server.AllowedPorts.IsInRange(TargetPort):
                    return {'status': 'error', 'message': f'Target port {TargetPort} not in allowed range'}
                if TargetPort in self.Server.GetAllUsedPorts():
                    return {'status': 'error', 'message': f'Target port {TargetPort} already in use'}
                Mode = Command.get('mode', 'tcp').lower()
                ForwardHost = Command.get('forward_host', '127.0.0.1')
                ForwardPort = Command.get('forward_port')
                if not ForwardPort:
                    return {'status': 'error', 'message': 'Forward port is required'}
                Success = False
                if Mode == 'tcp':
                    Success = self.CreateTcpMapping(ForwardHost, ForwardPort, TargetPort)
                else:
                    return {'status': 'error', 'message': f'Unsupported mode {Mode}'}
                if Success:
                    return {'status': 'success', 'message': f'Mapping created: {TargetPort} -> {ForwardHost}:{ForwardPort} ({Mode})'}
                else:
                    return {'status': 'error', 'message': 'Failed to create mapping'}
            elif CmdType == 'unregister':
                TargetPort = Command.get('target_port')
                if self.RemoveMapping(TargetPort):
                    return {'status': 'success', 'message': f'Mapping removed: {TargetPort}'}
                else:
                    return {'status': 'error', 'message': f'No mapping found for {TargetPort}'}
            else:
                return {'status': 'error', 'message': f'Unknown command type {CmdType}'}
        except Exception as E:
            self.HandleError(f"Error processing command: {str(E)}")
            return {'status': 'error', 'message': str(E)}
    def Run(self):
        try:
            self.ClientSocket.settimeout(30)
            while self.IsRunning:
                Data = b''
                while True:
                    try:
                        Chunk = self.ClientSocket.recv(1024)
                        if not Chunk:
                            self.Log("Connection closed by client")
                            self.Close()
                            return
                        Data += Chunk
                        if b'\n' in Data:
                            break
                    except socket.timeout:
                        continue
                    except Exception as E:
                        self.HandleError(f"Receive error: {str(E)}")
                        self.Close()
                        return
                try:
                    EncryptedData = Data.decode('utf-8').strip()
                    DecryptedData = self.Encryptor.Decrypt(EncryptedData)
                    Command = json.loads(DecryptedData)
                    Timestamp = Command.get('timestamp')
                    if not Timestamp or abs(time.time() - float(Timestamp)) > 30:
                        Response = {'status': 'error', 'message': 'Invalid or expired timestamp'}
                    else:
                        Response = self.ProcessCommand(Command)
                    Response['timestamp'] = str(time.time())
                    EncryptedResponse = self.Encryptor.Encrypt(json.dumps(Response))
                    self.ClientSocket.sendall((EncryptedResponse + '\n').encode('utf-8'))
                except Exception as E:
                    self.HandleError(f"Data processing error: {str(E)}")
                    Response = {'status': 'error', 'message': 'Invalid data format'}
                    EncryptedResponse = self.Encryptor.Encrypt(json.dumps(Response))
                    self.ClientSocket.sendall((EncryptedResponse + '\n').encode('utf-8'))
        except Exception as E:
            self.HandleError(f"Client handler error: {str(E)}")
        finally:
            self.Close()

class TcpMapping:
    def __init__(self, ClientHandler, ServerSocket, ForwardHost, ForwardPort, TargetPort):
        self.ClientHandler = ClientHandler
        self.ServerSocket = ServerSocket
        self.ForwardHost = ForwardHost
        self.ForwardPort = ForwardPort
        self.TargetPort = TargetPort
        self.IsRunning = True
        self.ClientHandler.Log(f"TCP mapping created: {TargetPort} -> {ForwardHost}:{ForwardPort}")
    def Log(self, Message):
        self.ClientHandler.Log(f"[TCP {self.TargetPort}] {Message}")
    def HandleError(self, Message):
        self.Log(f"Error: {Message}")
        self.Log(traceback.format_exc())
    def Close(self):
        self.IsRunning = False
        try:
            self.ServerSocket.close()
        except:
            pass
        self.Log("Mapping closed")
    def Relay(self, SrcSocket, DstSocket, Direction):
        try:
            while self.IsRunning:
                Data = SrcSocket.recv(4096)
                if not Data:
                    break
                DstSocket.sendall(Data)
                self.Log(f"Relayed {len(Data)} bytes {Direction}")
        except Exception as E:
            self.HandleError(f"Relay error {Direction}: {str(E)}")
        finally:
            try:
                SrcSocket.close()
            except:
                pass
            try:
                DstSocket.close()
            except:
                pass
    def HandleConnection(self, ClientSocket, Address):
        self.Log(f"New connection from {Address}")
        try:
            ForwardSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ForwardSocket.connect((self.ForwardHost, self.ForwardPort))
            self.Log(f"Connected to forward target {self.ForwardHost}:{self.ForwardPort}")
            threading.Thread(target=self.Relay, args=(ClientSocket, ForwardSocket, f"to {self.ForwardHost}:{self.ForwardPort}"), daemon=True).start()
            threading.Thread(target=self.Relay, args=(ForwardSocket, ClientSocket, f"from {self.ForwardHost}:{self.ForwardPort}"), daemon=True).start()
        except Exception as E:
            self.HandleError(f"Failed to connect to forward target: {str(E)}")
            try:
                ClientSocket.close()
            except:
                pass
    def Start(self):
        try:
            while self.IsRunning:
                self.ServerSocket.settimeout(1)
                try:
                    ClientSocket, Address = self.ServerSocket.accept()
                    ClientSocket.settimeout(None)
                    threading.Thread(target=self.HandleConnection, args=(ClientSocket, Address), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as E:
                    if self.IsRunning:
                        self.HandleError(f"Accept error: {str(E)}")
                    break
        except Exception as E:
            self.HandleError(f"Mapping error: {str(E)}")
        finally:
            self.Close()

class PortForwardServer:
    def __init__(self, InternalPort=5000, AllowedPortsRange="5001-5500", MaxPortsPerClient=5, Key="07A36AEF1907843"):
        self.InternalPort = InternalPort
        self.AllowedPorts = PortRange(AllowedPortsRange)
        self.MaxPortsPerClient = MaxPortsPerClient
        self.Key = Key
        self.ServerSocket = None
        self.IsRunning = False
        self.Clients = []
        self.ClientsLock = threading.Lock()
    def Log(self, Message):
        Timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{Timestamp}] [Server] {Message}")
    def HandleError(self, Message):
        self.Log(f"Error: {Message}")
        self.Log(traceback.format_exc())
    def GetAllUsedPorts(self):
        UsedPorts = set()
        with self.ClientsLock:
            for Client in self.Clients:
                UsedPorts.update(Client.Mappings.keys())
        return UsedPorts
    def RemoveClient(self, Client):
        with self.ClientsLock:
            if Client in self.Clients:
                self.Clients.remove(Client)
                self.Log(f"Client removed. Total clients: {len(self.Clients)}")
    def Start(self):
        try:
            self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ServerSocket.bind(('0.0.0.0', self.InternalPort))
            self.ServerSocket.listen(5)
            self.IsRunning = True
            self.Log(f"Server started on port {self.InternalPort}")
            self.Log(f"Allowed ports: {self.AllowedPorts.Start}-{self.AllowedPorts.End}")
            self.Log(f"Max ports per client: {self.MaxPortsPerClient}")
            while self.IsRunning:
                ClientSocket, Address = self.ServerSocket.accept()
                self.Log(f"New connection from {Address}")
                Client = ClientHandler(self, ClientSocket, Address)
                with self.ClientsLock:
                    self.Clients.append(Client)
                    self.Log(f"Client added. Total clients: {len(self.Clients)}")
                threading.Thread(target=lambda: [Client.Run(), self.RemoveClient(Client)], daemon=True).start()
        except Exception as E:
            self.HandleError(f"Server error: {str(E)}")
            self.Stop()
    def Stop(self):
        self.IsRunning = True
        if self.ServerSocket:
            try:
                self.ServerSocket.close()
            except:
                pass
        with self.ClientsLock:
            for Client in self.Clients:
                Client.Close()
            self.Clients.clear()
        self.Log("Server stopped")

if __name__ == "__main__":
    Config = {
        "internal_data_port": 5000,
        "allowed_port_range": "5001-5500",
        "max_ports_per_client": 5,
        "key": "07A36AEF1907843"
    }
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as F:
                Config.update(json.load(F))
        except Exception as E:
            print(f"Error loading config file: {str(E)}")
            os._exit(0)
    Server = PortForwardServer(
        InternalPort=int(Config["internal_data_port"]),
        AllowedPortsRange=Config["allowed_port_range"],
        MaxPortsPerClient=int(Config["max_ports_per_client"]),
        Key=Config["key"]
    )
    try:
        Server.Start()
    except KeyboardInterrupt:
        Server.Stop()
