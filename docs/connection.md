# 远程连接指南

qmtclient 只连接 qmtserver，不直接连接 MiniQMT，也不依赖 `xtquant`。策略机、服务器或笔记本只需要能访问运行 qmtserver 的 Windows 网关机器。

## 基本连接

```python
from qmtclient import QmtClient

client = QmtClient(
    "http://192.168.1.10:8000",
    token="dev-token",
)

print(client.health())
print(client.status())
```

`base_url` 写到 qmtserver 的服务根地址即可，默认 API 版本是 `/v1`。例如：

- `http://192.168.1.10:8000` 会访问 `http://192.168.1.10:8000/v1/health`。
- `https://qmt.example.com/qmt` 会访问 `https://qmt.example.com/qmt/v1/health`。
- WebSocket 会自动从 `http`/`https` 转换为 `ws`/`wss`。

## token

如果 qmtserver 配置了 token，qmtclient 会把 token 放入 HTTP `Authorization: Bearer ...` header。WebSocket 同时带 bearer header 和 `?token=` query，兼容浏览器和代理场景。

不要把真实 token 写入源码。推荐从环境变量读取：

```python
import os

from qmtclient import QmtClient

client = QmtClient(
    os.environ["QMTCLIENT_BASE_URL"],
    token=os.environ.get("QMTCLIENT_TOKEN"),
)
```

## LAN

局域网内使用网关机器 IP：

```powershell
$env:QMTCLIENT_BASE_URL = "http://192.168.1.10:8000"
$env:QMTCLIENT_TOKEN = "example-token"
uv run python examples/remote_connection.py
```

## VPN

通过 VPN 访问时，`base_url` 通常写 VPN 分配给网关机器的内网地址：

```powershell
$env:QMTCLIENT_BASE_URL = "http://10.8.0.5:8000"
$env:QMTCLIENT_TOKEN = "example-token"
uv run python examples/remote_connection.py
```

## 反向代理

通过 Nginx、Caddy 或其他反向代理访问时，建议使用 HTTPS：

```powershell
$env:QMTCLIENT_BASE_URL = "https://qmt.example.com/qmt"
$env:QMTCLIENT_TOKEN = "example-token"
uv run python examples/remote_connection.py
```

如果反向代理路径已经包含 `/v1`，可以显式关闭客户端的 API 版本前缀：

```python
client = QmtClient(
    "https://qmt.example.com/qmt/v1",
    token="example-token",
    api_version=None,
)
```

## qmtserver `/v1` 兼容性

qmtclient `0.1.0` 之前的基础 SDK 目标兼容 qmtserver `/v1`：

- `GET /v1/health`
- `GET /v1/qmt/status`
- `GET /v1/rpc/methods`
- `POST /v1/rpc`
- `GET /v1/orders`
- `GET /v1/orders/{order_id}`
- `GET /v1/trades`
- `GET /v1/events/recent`
- `WS /v1/ws/events`

客户端不会绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。交易相关调用是否允许执行，由 qmtserver 的服务端配置和保护逻辑决定。
