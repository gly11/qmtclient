# 更新日志

## 0.1.0 - 待发布

- 独立 `qmtclient` 包，兼容 qmtserver `/v1`。
- `QmtClient`：HTTP RPC、状态查询、订单/成交缓存、WebSocket 事件。
- 动态 RPC：`client.xtdata.<method>(...)`、`client.trader.<method>(...)`。
- 类型化异常：连接、认证、HTTP、协议、RPC。
- 策略接口：`client.market`、`client.account`、`client.trading`。
- 离线测试：`FakeQmtClient`、JSON/JSONL fixture、`EventReplay`。
- 示例：远程连接、策略接口、离线策略。
- typed package：`qmtclient/py.typed`。
