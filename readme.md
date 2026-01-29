<p align="center">
  <img src="https://avatars.githubusercontent.com/u/193612261?v=4" width="270px" />
  <p align="center">PyFrp</p>
  <p align="center">Frp (Fast Reverse Proxy) implemented in Python</p>
</p>

![GitHub Followers](https://img.shields.io/badge/dynamic/json?color=green&label=GitHub%20Followers&query=%24.data.totalSubs&url=https%3A%2F%2Fapi.spencerwoo.com%2Fsubstats%2F%3Fsource%3Dgithub%26queryKey%3DGVSADS)
![Total Repos](https://img.shields.io/badge/dynamic/json?color=orange&label=Total%20Repos&query=%24.total_count&url=https%3A%2F%2Fapi.github.com%2Fsearch%2Frepositories%3Fq%3Duser%3AGVSADS)

---

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Operating System](https://img.shields.io/badge/Operating%20System-000000?style=for-the-badge&logo=linux&logoColor=white)
![Server](https://img.shields.io/badge/Server-000000?style=for-the-badge&logo=serverless&logoColor=white)
![Networking](https://img.shields.io/badge/Networking-000000?style=for-the-badge&logo=cisco&logoColor=white)

---
> **This project is only in its early stages, and the documentation is currently being improved. Thank you for using this project. If possible, please give it a star ♥**

# PyFrp

## 🗡 Brief Introduction
The original Frp (https://github.com/Fatedier/frp/) is somewhat bloated in size, while PyFrp is a simplified Python-based implementation with a smaller footprint and fewer features.

### Comparison with the Original Frp
| Feature| PyFrp | Frp|
|:---------------:|:-----:|:----:|
| Quick Setup| ✅| ✅|
| Size| ✅| ❌|
| SSL Support| ❌| ✅|
| Embeddable| ✅| ✅❌ |
| Documentation| ✅| ✅|
| TCP Support| ✅| ✅|
| UDP Support| ❌| ✅|
| HTTP/HTTPS Support| ❌| ✅|

Choose based on your needs:
- If you prioritize **quick setup, small size, simplicity, and embeddability** (e.g., integrating into your Python project), PyFrp is a great choice.
- For **production deployments**, Frp remains the better option for now.

In the future, we aim to enhance PyFrp's functionality, add more configuration options, and potentially support additional protocols (e.g., HTTP/HTTPS).

We’re just getting started and would greatly appreciate your support—**a ⭐ Star** would mean a lot to us!

> Note: **HTTPS is not yet supported**. We may add this later, and contributions are welcome!

---

## 🚀 Quick Start

### Prerequisites

The only third-party library you need is `pycryptodome`. Install it with:
```bash
pip install pycryptodome
```
While any version of `pycryptodome` should work, we recommend **v3.22.0** if you encounter issues:
```bash
pip install pycryptodome==3.22.0
```

### Configuration

#### Server (`server_config.json`):
```json
{
    "InternalDataPort": 5000, // PyFrp server data port
    "AllowedPortRange": "5001-5500", // Allowed port range
    "MaxPortsPerClient": 5, // Max ports per client
    "Key": "07A36AEF1907843" // Authentication key
}
```

#### Client (`client_config.json`):
```json
{
    "ServerDomain": "127.0.0.1", // PyFrp server address
    "ServerPort": 5000, // PyFrp server port
    "Key": "07A36AEF1907843", // Authentication key
    "Forwards": [ // Port mappings
        {
            "forward_domain": "127.0.0.1", // Local host
            "forward_port": 36667, // Local port
            "target_port": 5002, // Target port
            "mode": "TCP" // Protocol (TCP only)
        }
        // Add more mappings as needed
    ]
}
```

### Running PyFrp

#### Start the server:
```bash
python server.py server_config.json
```

#### Start the client:
```bash
python client.py client_config.json
```

You can also modify the default configuration directly in the source code.

---

## 📖 Usage Example

### Example: Exposing a Local HTTP Server

1. **Start a local HTTP server**:
   ```bash
   python -m http.server 36667
   ```

2. **Configure PyFrp client** (`client_config.json`):
   ```json
   {
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
   ```

3. **Start PyFrp server and client**:
   ```bash
   # In terminal 1
   python server.py
   
   # In terminal 2
   python client.py
   ```

4. **Access the local server through the proxy**:
   ```bash
   curl http://localhost:5002
   ```

   You should see the HTTP response from your local server, indicating that the port forwarding is working correctly.

---

## ⚠️ Limitations

- **Only TCP protocol is supported** (UDP, HTTP, HTTPS are not supported)
- **No SSL encryption** for data transmission
- **Simple authentication mechanism** (fixed key)
- **No automatic reconnection** after network interruption
- **Limited error handling** and logging
- **Performance limitations** due to JSON and hex encoding for data transfer

---

## 🛠️ How It Works

### Server-side (server.py)
1. Listens for client connections on the internal data port
2. Handles client authentication
3. Creates and manages port forwarding services
4. Forwards data between external connections and clients

### Client-side (client.py)
1. Connects to the server and authenticates
2. Sends port forwarding configuration
3. Handles connections to local services
4. Forwards data between the server and local services

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** by opening an issue
2. **Suggest features** by opening an issue
3. **Submit pull requests** with bug fixes or enhancements

### Development Guidelines
- Follow the existing code style
- Add comments for complex code
- Test your changes thoroughly
- Update documentation as needed

---

## 📞 Contact Us
 - 📧 Email: wyt18222152539wyt@163.com
 - 🌐 Website: [Galaxy Vastar Software Studio](https://www.gvsds.com)
 - 📱 WeChat: GVSADS

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 🗡 简单介绍
原本的 Frp https://github.com/Fatedier/frp/ 体积略显臃肿，而 PyFrp 则是一个基于 Python 实现的简单版本，体积更小，功能也更简单。

我们 和 原版 Frp 相比
| 功能 | PyFrp | Frp |
|:-:|:-:|:-:|
| 快速配置 | ✅ | ✅ |
| 体积 | ✅ | ❌ |
| SSL 功能 | ❌ | ✅ |
| 嵌入式 | ✅ | ✅❌ |
| 文档 | ✅ | ✅ |
| TCP 支持 | ✅ | ✅ |
| UDP 支持 | ❌ | ✅ |
| HTTP/HTTPS 支持 | ❌ | ✅ |

请您根据您的需要选择使用哪个，
- 如果您需要快速配置，体积小，功能简单，嵌入式，集成到您自己的 Python 项目中，那么 PyFrp 是一个不错的选择。
- 如果您需要部署在生产环境中，暂时不要选择 PyFrp，Frp 是一个更好的选择。

日后，我们以 Frp 为目标，完善其功能，添加更多的配置项，同时也会考虑添加更多的协议支持，如 http、https 等。

我们其实也才起步，仍然需要您的支持，如果可以，还请您点一个 Star ⭐，这将是对我们最大的支持。

> 注意，我们暂时还不支持 https 协议。稍后如果有时间，我们可能会考虑支持，如果您已经帮我们支持，随时欢迎您提交。

## 🚀 快速开始

### 先决条件

你唯一需要下载的第三方库是 `pycryptodome`，使用以下命令安装：
```bash
pip install pycryptodome
```
我们推荐使用 **v3.22.0** 版本：
```bash
pip install pycryptodome==3.22.0
```

### 配置

#### 服务器端配置 (`server_config.json`)：
```json
{
    "InternalDataPort": 5000, // PyFrp 服务器端数据端口
    "AllowedPortRange": "5001-5500", // 允许的端口范围
    "MaxPortsPerClient": 5, // 每个客户端最大端口数
    "Key": "07A36AEF1907843" // 认证密钥
}
```

#### 客户端配置 (`client_config.json`)：
```json
{
    "ServerDomain": "127.0.0.1", // PyFrp 服务器端主机地址
    "ServerPort": 5000, // PyFrp 服务器端端口
    "Key": "07A36AEF1907843", // 认证密钥
    "Forwards": [ // 端口映射配置
        {
            "forward_domain": "127.0.0.1", // 本地主机地址
            "forward_port": 36667, // 本地端口
            "target_port": 5002, // 目标端口
            "mode": "TCP" // 传输模式（仅支持TCP）
        }
        // 你可以在这里输入更多的端口映射配置
    ]
}
```

### 运行 PyFrp

#### 启动服务器：
```bash
python server.py server_config.json
```

#### 启动客户端：
```bash
python client.py client_config.json
```

你也可以直接修改源代码中的默认配置。

---

## � 使用示例

### 示例：暴露本地 HTTP 服务器

1. **启动本地 HTTP 服务器**：
   ```bash
   python -m http.server 36667
   ```

2. **配置 PyFrp 客户端** (`client_config.json`)：
   ```json
   {
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
   ```

3. **启动 PyFrp 服务器和客户端**：
   ```bash
   # 在终端 1 中
   python server.py
   
   # 在终端 2 中
   python client.py
   ```

4. **通过代理访问本地服务器**：
   ```bash
   curl http://localhost:5002
   ```

   你应该会看到来自本地服务器的 HTTP 响应，表明端口转发工作正常。

---

## ⚠️ 限制

- **仅支持 TCP 协议**（不支持 UDP、HTTP、HTTPS）
- **数据传输无 SSL 加密**
- **简单的认证机制**（固定密钥）
- **网络中断后无自动重连**
- **有限的错误处理**和日志记录
- **性能限制**（由于使用 JSON 和 hex 编码传输数据）

---

## 🛠️ 工作原理

### 服务器端 (server.py)
1. 在内部数据端口上监听客户端连接
2. 处理客户端认证
3. 创建和管理端口转发服务
4. 在外部连接和客户端之间转发数据

### 客户端 (client.py)
1. 连接到服务器并进行认证
2. 发送端口转发配置
3. 处理到本地服务的连接
4. 在服务器和本地服务之间转发数据

---

## 🤝 贡献

欢迎贡献！你可以通过以下方式帮助我们：

1. **报告错误**：通过打开 issue
2. **建议功能**：通过打开 issue
3. **提交代码**：通过 pull request 提交 bug 修复或增强功能

### 开发指南
- 遵循现有的代码风格
- 为复杂代码添加注释
- 彻底测试你的更改
- 根据需要更新文档

---

## �📞 联系我们
 - 📧 Email: wyt18222152539wyt@163.com
 - 🌐 官网: [银河万通软件开发工作室](https://www.gvsds.com)
 - 📱 微信: GVSADS

---

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。
