# HANDOFF — Caliper（2026-11-13 收口）

> 下一个会话/下一个人从这里开始。只读本页 + 方案 §6 的对应天，不要通读整份方案。
> 方案定稿：`C:\Users\69561\Desktop\AI个人项目方案汇总.md`（v3.4，26 天 / 208h）

---

## 0. 一句话状态

D0（环境 + 骨架）已完成并验收：仓库上线、CI 双平台绿、venv/依赖/模型/Docker/镜像/.env/API 全就绪。
**下一步 D1（11-16 周一）：Provider 适配器 + 最小 loop + trace v1。**

---

## 1. 地址

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/reachformoon/Caliper （public，main） |
| CI | `.github/workflows/ci.yml`，Ubuntu + Windows 双绿 |
| 方案 | `C:\Users\69561\Desktop\AI个人项目方案汇总.md`（v3.4） |
| 横评规范 | `docs/Caliper-同类横评实现规范.md` |
| D0 手册 | `docs/D0-手工步骤.md` |
| 30 题清单 | `docs/D0-30题清单.md` |
| 旧文档 | `legacy/2026-10-caliper/`（**不要按里面排期执行**） |

---

## 2. D0 已完成（证据）

- Python **3.13.9**（`C:\ProgramData\anaconda3\python.exe`）+ `.venv`（288MB）
- 依赖：pydantic 2.14.3、typer 0.29.1、rich、httpx、pyyaml、pytest 9.2.0、fastembed 0.9.1、sqlite-vec 0.1.9、**mcp 2.3.0**
- 嵌入模型 `BAAI/bge-small-zh-v1.5`（512 维），经 `hf-mirror.com` 下载（`scripts/fetch_model.py`）
- Docker **29.9.3** + Compose **5.7.0**；镜像 `postgres:16`、`pgvector/pgvector:pg16`、`hello-world`
- WSL：**4GB / swap 2GB / 4 核**，实测 Docker VM 4.01GiB、Ubuntu 3916MB
- `.env`：`deepseek-flash`，真实调用 HTTP 200，`reasoning_tokens` 已确认
- 质量闸：`check_core_purity.py` OK、pytest 4 passed、`cal demo` 离线可跑
- 30 题清单（配额：≥12 通过率、≥8 跨文件、≥6 跨工具、≥4 长周期）

---

## 3. 环境事实（别重新踩）

| 事实 | 说明 |
|---|---|
| 宿主内存 | **16GB**（旧结论 7GB 有误） |
| 系统代理 | `127.0.0.1:7897`；`github.com` 直连被重置、`api.github.com` 直连可用 |
| git 代理 | 仓库本地 `http.proxy=http://127.0.0.1:7897`；Clash 换端口要改 |
| Docker Hub | 直连不通；`~/.docker/daemon.json` 已配 `docker.m.daocloud.io` + `docker.1panel.live` |
| Docker Desktop | **必须从开始菜单启动**；从 agent shell 启动会被回收（`0x40010004`） |
| bash PATH | DSH 的 MSYS PATH 被改坏（盘符拆开），bash 里直接 `docker` 会 126；用 PowerShell 或全路径 |
| Windows 控制台 | 默认 cp1252；CLI 已强制 UTF-8，CI 有 `PYTHONUTF8=1` |
| mcp SDK | `mcp==2.3.0` 是 **v2 API**（`Client` / `StdioServerParameters`）；全局 1.28.1 是 v1 |
| 模型名 | 官方只认 `deepseek-flash` / `deepseek-v4-pro`；`deepseek-v4.1-flash` 会 400 |
| reasoning | `deepseek-flash` 返回 `reasoning_content`；`max_tokens` 太小 content 为空（建议 ≥512）；reasoning 不要回灌 |
| 模型缓存 | 已下载；换机器跑 `python scripts/fetch_model.py` |

---

## 4. 关键决策（已定）

1. 架构不变：Python-only + SQLite；**不做 LangGraph**（ADR-001）、**不做 Redis**（为耐久层让路）。
2. 耐久层进核心 D3–D5：checkpoint / 断点续跑 / 人工审批，自研（ADR-002）。
3. 企业栈后置：Docker D18 → FastAPI D19 → PG/pgvector D20–D21（`CALIPER_PROFILE=stack`）；默认 `light`。
4. 薄前端只读 D22–D23：消费 `cal export --json`，零写接口，不是运行时依赖。
5. 评测闸门：三态判决 + MDE；能力默认关闭，PASS 才写 `capabilities.lock`。

---

## 5. 代码现状

```
pyproject.toml                # extras: mcp / rag / api / pg / dev
src/caliper/
  cli.py                      # version/demo/doctor 已实现；其余为占位（exit 2）
  core/models.py              # Run/Step/Checkpoint/Approval/Budget/RunResult
  core/protocols.py           # Store/Queue/Orchestrator/RunnerService（只有协议）
  adapters/                   # 空；D1 起放 openai_provider / fake_provider / sqlite_store
scripts/check_core_purity.py  # 内核零污染检查（进 CI）
scripts/fetch_model.py        # 模型下载（hf-mirror）
tests/                        # 4 passed
```

---

## 6. 下一步 D1

目标：`cal demo` 仍离线可跑；新增一次真实运行产出 `trace.jsonl`，`cal trace show` / `cal cost` 可读。

1. `adapters/openai_provider.py`：httpx 调 `/chat/completions`；处理 `reasoning_content`、usage（含 `reasoning_tokens`）、超时/重试。
2. `adapters/fake_provider.py`：确定性 6 步，供离线 demo 与测试。
3. ToolRegistry：JSON Schema + pydantic 校验、并行调用、结果截断。
4. 最小 loop：run.start → step → llm.request/response → tool.call/result → run.end。
5. trace schema v1（JSONL）+ `cal trace show` + `cal cost`（含 reasoning）。
6. 测试：httpx MockTransport 测 provider；fake provider 测 loop；purity 仍绿。

验收：4 tests 全绿 + 1 个真实 run 的 trace 可读 + `cal cost` 与 usage 对得上。

---

## 7. 命令速查

```powershell
cd D:\Caliper
.venv\Scripts\activate
python -m pytest -q
python scripts/check_core_purity.py
python -m caliper doctor
python -m caliper demo
python scripts/fetch_model.py
docker compose version
docker images
```

---

## 8. 不要做

- 不要把 `.env` 提交（已 gitignore）；API key 曾出现在会话记录，项目稳定后轮换。
- 不要用 `deepseek-v4.1-flash`（400）；用 `deepseek-flash`。
- 不要从 agent shell 启动 Docker Desktop。
- 不要在 D18 前引入 FastAPI/PG；不做 LangGraph/Redis。
- 不要通读整份方案；只读 §6 对应天 + 本页。
- GitHub PAT 不落盘；推送时重新提供（Contents + Workflows 权限）。

---

## 9. 上下文策略

- 本会话上下文已接近上限（粗估 70–90%），不适合继续做 D1 之后的实现。
- 每 2–3 天或每个阶段开新会话，开场白固定：

> 读 `D:\Caliper\HANDOFF.md`，从 D<n> 开始，先给 5 行计划再动手。

- 每天收工更新本文件 §0 / §2 / §6。
- 大文件不要整份读；用 §6 的行 + 本页。

---

## 10. 变更记录

- 2026-11-13：D0 完成；仓库上线、CI 双绿；耐久层/企业栈/前端排期定稿；写入本交接。
