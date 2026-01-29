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
> **This project is only in its early stages, and the documentation is currently incomplete. Thank you for using this project. If possible, please give it a star ♥**

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
| Documentation| ❌| ✅|

Choose based on your needs:
- If you prioritize **quick setup, small size, simplicity, and embeddability** (e.g., integrating into your Python project), PyFrp is a great choice.
- For **production deployments**, Frp remains the better option for now.

In the future, we aim to enhance PyFrp's functionality, add more configuration options, and potentially support additional protocols (e.g., HTTP/HTTPS).

We’re just getting started and would greatly appreciate your support—**a ⭐ Star** would mean a lot to us!

If needed, we could also develop a **C-based implementation** of Frp.

> Note: **HTTPS is not yet supported**. We may add this later, and contributions are welcome!

---

## 🚀 Quick Start

The only third-party library you need is `pycryptodome`. Install it with:
```bash
pip install pycryptodome
```
We use its encryption algorithms to secure your data. While any version of `pycryptodome` should work, we recommend **v3.22.0** if you encounter issues:
```bash
pip install pycryptodome==3.22.0
```
For a **non-encrypted version**, simply remove all encryption-related code.

### Configuration
#### Server (`server_config.json`):
```python
{
    "internal_data_port": 5000, // PyFrp server data port
    "allowed_port_range": "5001-5500", // Allowed port range
    "max_ports_per_client": 5, // Max ports per client
    "key": "07A36AEF1907843" // Encryption key
}
```

#### Client (`client_config.json`):
```python
{
    "server_host": "127.0.0.1", // PyFrp server address
    "server_port": 5000, // PyFrp server port
    "key": "07A36AEF1907843", // Encryption key
    "mappings": [ // Port mappings
        {
            "forward_host": "127.0.0.1", // Local host
            "forward_port": 5902, // Local port
            "target_port": 5500, // Target port
            "mode": "tcp" // Protocol (TCP/UDP)
        }
        // Add more mappings as needed
    ]
}
```

Run with custom configs:
```bash
python server.py server_config.json
python client.py client_config.json
```

---

## 📞 Contact Us
 - 📧 Email: wyt18222152539wyt@163.com
 - 🌐 Website: [Galaxy Vastar Software Studio](https://www.gvsds.com)
 - 📱 WeChat: GVSADS

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
| 文档 | ❌ | ✅ |

请您根据您的需要选择使用哪个，
- 如果您需要快速配置，体积小，功能简单，嵌入式，集成到您自己的 Python 项目中，那么 PyFrp 是一个不错的选择。
- 如果您需要部署在生产环境中，暂时不要选择 PyFrp，Frp 是一个更好的选择。

日后，我们以 Frp 为目标，完善其功能，添加更多的配置项，同时也会考虑添加更多的协议支持，如 http、https 等。

我们其实也才起步，仍然需要您的支持，如果可以，还请您点一个 Star ⭐，这将是对我们最大的支持。

如果您有需要，我们可以设计一版 C 实现的 Frp。

> 注意，我们暂时还不支持 https 协议。稍后如果有时间，我们可能会考虑支持，如果您已经帮我们支持，随时欢迎您提交。

## 🚀 快速开始

你唯一需要下载的第三方库是 `pycryptodome`，使用以下命令安装：
```bash
pip install pycryptodome
```
我们使用它的加密算法来保护你的数据。我们可知的是任意版本的 `pycryptodome` 都可以使用。但如果出现加密算法的报错，我们建议你使用最新版本的 `pycryptodome`，或者使用我们所使用的 3.22.0 版本，即：
```bash
pip install pycryptodome==3.22.0
```
如果你期望使用一个不带加密的版本，你可以将所有涉及加密的部分全部删掉。



然后，你可以修改源代码中的个人配置

server端配置修改：
```python
{
    "internal_data_port": 5000, // PyFrp 服务器端数据端口
    "allowed_port_range": "5001-5500", // 允许的端口范围
    "max_ports_per_client": 5, // 每个客户端最大端口数
    "key": "07A36AEF1907843" // 加密密钥
}
```

client
```python
{
    "server_host": "127.0.0.1", // PyFrp 服务器端主机地址
    "server_port": 5000, // PyFrp 服务器端端口
    "key": "07A36AEF1907843", // 加密密钥
    "mappings": [ // 端口映射配置
        {
            "forward_host": "127.0.0.1", // 本地主机地址
            "forward_port": 5902, // 本地端口
            "target_port": 5500, // 目标端口
            "mode": "tcp" // 传输模式
        },
        // 你可以在这里输入更多的端口映射配置
    ]
}
```

允许你直接修改代码中尾部的 Config 变量来实现自定义配置。或者指定配置文件位置。
```bash
python server.py server_config.json
python client.py client_config.json
```

## 📞 联系我们
 - 📧 Email: wyt18222152539wyt@163.com
 - 🌐 官网: [银河万通软件开发工作室](https://www.gvsds.com)
 - 📱 微信: GVSADS
