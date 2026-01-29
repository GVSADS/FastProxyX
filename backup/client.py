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

class PortMapping:
    def __init__(self, ForwardHost, ForwardPort, TargetPort, Mode):
        self.ForwardHost = ForwardHost
        self.ForwardPort = ForwardPort
        self.TargetPort = TargetPort
        self.Mode = Mode.lower()
        self.IsActive = False
    def ToDict(self):
        return {
            'forward_host': self.ForwardHost,
            'forward_port': self.ForwardPort,
            'target_port': self.TargetPort,
            'mode': self.Mode
        }

class PortForwardClient:
    def __init__(self, ServerHost="127.0.0.1", ServerPort=5000, Key="07A36AEF1907843"):
        self.ServerHost = ServerHost
        self.ServerPort = ServerPort
        self.Key = Key
        self.Socket = None
        self.IsRunning = False
        self.Mappings = []
        self.MappingsLock = threading.Lock()
        self.Encryptor = AesEncryptor(Key)
    def Log(self, Message):
        Timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{Timestamp}] [Client] {Message}")
    def HandleError(self, Message):
        self.Log(f"Error: {Message}")
        self.Log(traceback.format_exc())
    def Connect(self):
        try:
            self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Socket.connect((self.ServerHost, self.ServerPort))
            self.Log(f"Connected to server {self.ServerHost}:{self.ServerPort}")
            return True
        except Exception as E:
            self.HandleError(f"Connection failed: {str(E)}")
            self.Socket = None
            return False
    def AddMapping(self, ForwardHost, ForwardPort, TargetPort, Mode):
        with self.MappingsLock:
            for M in self.Mappings:
                if M.TargetPort == TargetPort:
                    self.Log(f"Mapping for target port {TargetPort} already exists")
                    return False
            Mapping = PortMapping(ForwardHost, ForwardPort, TargetPort, Mode)
            self.Mappings.append(Mapping)
            # 仅当已连接时才立即注册映射
            if self.Socket is not None:
                return self.RegisterMapping(Mapping)
            return True  # 连接后会自动注册
    def RegisterMapping(self, Mapping):
        if self.Socket is None:
            self.Log("Cannot register mapping - not connected to server")
            return False
        try:
            Command = {
                'type': 'register',
                'timestamp': str(time.time()),
                **Mapping.ToDict()
            }
            EncryptedData = self.Encryptor.Encrypt(json.dumps(Command))
            self.Socket.sendall((EncryptedData + '\n').encode('utf-8'))
            ResponseData = self.Socket.recv(4096).decode('utf-8').strip()
            Response = json.loads(self.Encryptor.Decrypt(ResponseData))
            if Response.get('status') == 'success':
                self.Log(f"Successfully registered mapping: {Mapping.TargetPort} -> {Mapping.ForwardHost}:{Mapping.ForwardPort} ({Mapping.Mode})")
                Mapping.IsActive = True
                return True
            else:
                self.Log(f"Failed to register mapping: {Response.get('message', 'Unknown error')}")
                return False
        except Exception as E:
            self.HandleError(f"Error registering mapping: {str(E)}")
            return False
    def RemoveMapping(self, TargetPort):
        with self.MappingsLock:
            for I, M in enumerate(self.Mappings):
                if M.TargetPort == TargetPort:
                    if self.UnregisterMapping(M):
                        del self.Mappings[I]
                        return True
                    return False
            self.Log(f"No mapping found for target port {TargetPort}")
            return False
    def UnregisterMapping(self, Mapping):
        try:
            Command = {
                'type': 'unregister',
                'timestamp': str(time.time()),
                'target_port': Mapping.TargetPort
            }
            EncryptedData = self.Encryptor.Encrypt(json.dumps(Command))
            self.Socket.sendall((EncryptedData + '\n').encode('utf-8'))
            ResponseData = self.Socket.recv(4096).decode('utf-8').strip()
            Response = json.loads(self.Encryptor.Decrypt(ResponseData))
            if Response.get('status') == 'success':
                self.Log(f"Successfully unregistered mapping: {Mapping.TargetPort}")
                Mapping.IsActive = False
                return True
            else:
                self.Log(f"Failed to unregister mapping: {Response.get('message', 'Unknown error')}")
                return False
        except Exception as E:
            self.HandleError(f"Error unregistering mapping: {str(E)}")
            return False
    def Start(self):
        if not self.Connect():
            return
        self.IsRunning = True
        self.Log("Client started")
        try:
            # 连接成功后注册所有映射
            with self.MappingsLock:
                for Mapping in self.Mappings:
                    self.RegisterMapping(Mapping)
            while self.IsRunning:
                time.sleep(1)
        except KeyboardInterrupt:
            self.Log("Client interrupted")
        except Exception as E:
            self.HandleError(f"Client error: {str(E)}")
        finally:
            self.Stop()
    def Stop(self):
        self.IsRunning = False
        with self.MappingsLock:
            for Mapping in self.Mappings:
                if Mapping.IsActive:
                    self.UnregisterMapping(Mapping)
            self.Mappings.clear()
        if self.Socket:
            try:
                self.Socket.close()
            except:
                pass
        self.Log("Client stopped")


if __name__ == "__main__":
    Config = {
        "server_host": "127.0.0.1",
        "server_port": 5000,
        "key": "07A36AEF1907843",
        "mappings": [
            {
                "forward_host": "127.0.0.1",
                "forward_port": 5902,
                "target_port": 5500,
                "mode": "tcp"
            }
        ]
    }
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as F:
                Config.update(json.load(F))
        except Exception as E:
            print(f"Error loading config file: {str(E)}")
            os._exit(0)
    Client = PortForwardClient(
        ServerHost=Config["server_host"],
        ServerPort=int(Config["server_port"]),
        Key=Config["key"]
    )
    for Mapping in Config["mappings"]:
        Client.AddMapping(
            ForwardHost=Mapping["forward_host"],
            ForwardPort=int(Mapping["forward_port"]),
            TargetPort=int(Mapping["target_port"]),
            Mode=Mapping["mode"]
        )
    try:
        Client.Start()
    except KeyboardInterrupt:
        Client.Stop()