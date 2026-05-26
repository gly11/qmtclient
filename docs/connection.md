# 远程连接

`base_url` 写 qmtserver 服务根地址，默认自动加 `/v1`。

```python
from qmtclient import QmtClient

client = QmtClient("http://192.168.1.10:8000", token="dev-token")
print(client.health())
```

## 诊断

`diagnose()` 会聚合 HTTP、server ready、RPC methods 和可选只读 sample 检查。单项失败不会中断整体诊断。

```python
result = client.diagnose(sample_code="000001.SZ")
print(result["ok"])
for check in result["checks"]:
    print(check["name"], check["ok"])
```

返回结构使用 `schema_version="qmtclient.diagnose.v1"`。真实 qmtserver 诊断只作为手动冒烟检查，不是默认单元测试门禁。

## 地址示例

| 场景 | `base_url` |
| --- | --- |
| LAN | `http://192.168.1.10:8000` |
| VPN | `http://10.8.0.5:8000` |
| 反向代理 | `https://qmt.example.com/qmt` |

WebSocket 会自动从 `http`/`https` 转成 `ws`/`wss`。

## token

HTTP 使用 `Authorization: Bearer ...`。WebSocket 同时携带 bearer header 和 `?token=`。

推荐从环境变量读取：

```python
import os

client = QmtClient(
    os.environ["QMTCLIENT_BASE_URL"],
    token=os.environ.get("QMTCLIENT_TOKEN"),
    timeout=10.0,
    retries=1,
)
```

## 已包含 `/v1` 的代理路径

```python
client = QmtClient(
    "https://qmt.example.com/qmt/v1",
    token="example-token",
    api_version=None,
)
```

## qmtserver `/v1`

qmtclient 默认目标兼容 qmtserver `/v1`：

- `GET /v1/health`
- `GET /v1/qmt/status`
- `GET /v1/rpc/methods`
- `POST /v1/rpc`
- `GET /v1/orders`
- `GET /v1/orders/{order_id}`
- `GET /v1/trades`
- `GET /v1/events/recent`
- `WS /v1/ws/events`
