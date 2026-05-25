# 发布准备

本文记录 qmtclient `0.1.0` 的 release readiness 要求。

## 发布目标

`0.1.0` 是 qmtclient 从 `qmtserver.client` 拆出后的第一个独立客户端 SDK 版本。发布前必须满足：

- 没有 MiniQMT 的电脑可以使用 `QmtClient` 调用远程 qmtserver。
- 策略代码不需要导入 `xtquant`。
- 常见行情、账户、委托和事件 helper 有测试覆盖。
- 离线策略测试可以使用 fake client、fixtures 和 event replay。
- qmtserver `/v1` API 兼容性已文档化。

## 发布前检查

```powershell
uv sync
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
```

## 包检查

发布前需要确认：

- `pyproject.toml` 版本与 `qmtclient.__version__` 一致。
- wheel 中包含 `qmtclient/py.typed`。
- wheel 中不包含 `.venv/`、缓存目录、真实 token、真实账号、个人路径、MiniQMT 用户数据或日志。
- README 可以作为项目长描述读取。
- `uv.lock` 与 `pyproject.toml` 版本一致。

## 版本规则

M1-M3 完成时保持开发版本。M4 通过 release readiness 后，版本切到 `0.1.0`。

后续补丁版本建议：

- `0.1.x`：保持 qmtserver `/v1` 兼容，修复 bug 或补充轻量 helper。
- `0.2.0`：新增较大的客户端行为、兼容策略或 qmtserver 新 API 版本支持。

## 不属于发布内容

- 不发布 qmtserver。
- 不发布 MiniQMT 或 `xtquant`。
- 不提供 GUI。
- 不提供真实 token、真实账号或个人路径。
- 不承诺直接连接 MiniQMT。
