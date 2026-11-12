# Caliper

[![ci](https://github.com/reachformoon/Caliper/actions/workflows/ci.yml/badge.svg)](https://github.com/reachformoon/Caliper/actions/workflows/ci.yml)

> 一个轻量、可扩展的 coding-agent harness：**扩展能力默认关闭，只有通过评测闸门的能力才允许写进默认配置。**

CLI：`cal` · 核心 Python 3.11+ · 默认零外部服务（SQLite + 进程内队列）

## 当前状态

> 接续工作请先读 [HANDOFF.md](HANDOFF.md)。


骨架阶段（D0/D1）。完整 26 天计划见 `docs/README.md` 指向的定稿方案。

## 快速开始

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -e ".[dev]"
cal version
cal demo
cal doctor
```

## 设计约束（进 CI）

1. 内核（`src/caliper/core`）不 import `fastapi` / `langgraph` / `redis` / `psycopg` / `sqlite3`。
2. 内核不 `print()`、不 `sys.exit()`，返回对象由 CLI/API 渲染。
3. 路径只走 `pathlib`，不写死盘符。
4. `pip install caliper-harness`（不带 extras）能跑全部测试。
