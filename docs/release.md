# 发布检查

`0.1.0` 发布前运行：

```powershell
uv sync
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
uv tool run twine check dist/*
```

## CI

GitHub Actions 覆盖：

- Windows、macOS、Linux。
- Python 3.10、3.11、3.12、3.13、3.14。
- unittest、ruff、format check、ty、build、twine check。

## 包检查

- `pyproject.toml` 版本与 `qmtclient.__version__` 一致。
- wheel 包含 `qmtclient/py.typed`。
- wheel 不包含 `.venv/`、缓存、真实 token、真实账号、个人路径、MiniQMT 数据或日志。
- `uv.lock` 与 `pyproject.toml` 版本一致。

## 不发布

- qmtserver。
- MiniQMT 或 `xtquant`。
- GUI。
- 真实 token、真实账号或个人路径。
