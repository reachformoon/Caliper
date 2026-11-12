# 技术栈可行性与 14 天风险验证（结论页）

> 验证日 2026-10-30；版本号取自当日 PyPI。未抓到的写「未验证」，不猜。

## 0. 总判断
- **能做，但只能窄做**：112h 里约 40h 会被环境/联调吃掉，净编码 ~70h。
- 最危险的不是 MCP（1 天内可通），是 **RAG 效果**与**多 Agent 调试**。
- 锁版本：mcp==2.3.0、sqlite-vec==0.1.9、fastembed==0.9.1、rank-bm25==0.2.2。

## 1. MCP Python SDK（结论：1 天内能通 stdio，前提锁 2.x）
- 包名 `mcp`，PyPI 最新 **2.3.0**，requires-python **>=3.10**；装 `pip install "mcp[cli]"`。https://pypi.org/project/mcp/
- v2 已是稳定版，`pip install mcp` 装 2.x；v1 进维护线，要留 1.x 必须写 `mcp>=1.28,<2`。https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/README.md
- 因此网上大量 `ClientSession` 教程是 **v1 API**，照抄会崩（v1：`from mcp import ClientSession` + `stdio_client`）。
- v2 client 骨架（官方形态，可跑）：
```python
import anyio
from mcp import Client, StdioServerParameters

server = StdioServerParameters(command="python", args=["server.py"], env={"API_KEY": "x"})

async def main() -> None:
    async with Client(server) as client:      # 进入即 spawn 子进程 + 握手
        tools = await client.list_tools()
        print([t.name for t in tools.tools])
        r = await client.call_tool("search", {"q": "hi"})
        print(r.structured_content, r.is_error)   # 结构体 / 失败标记

anyio.run(main)
```
- server 侧：`from mcp.server import MCPServer` + `@mcp.tool()` + `mcp.run()`（无参默认 stdio）。
- 坑：stdio 下 **stdout 就是协议线**，任何 print 会污染流；日志只能 stderr/logging。
- 文档：https://py.sdk.modelcontextprotocol.io/client/transports/ 、https://py.sdk.modelcontextprotocol.io/run/
- 判定：环境 + hello world 半天；list/call/超时/子进程回收 1 天内可达。Streamable HTTP 另算 0.5 天，首版不做。

## 2. SKILL.md（结论：照标准写，1 天够；别自创字段）
- 标准（agentskills.io）：必填 `name`(≤64，小写+连字符)、`description`(≤1024)；可选 `license`、`compatibility`(≤500)、`metadata`(string map)、`allowed-tools`(空格分隔，标注 **Experimental**)。
- 三级渐进加载：① metadata ~100 tokens 全量常驻 → ② 命中后载入正文（建议 <5000 tokens / <500 行）→ ③ `scripts/ references/ assets/` 按需读取。
- Claude Code 扩展字段：`disallowed-tools`、`when_to_use`、`argument-hint`、`arguments`、`disable-model-invocation`、`user-invocable`、`model`、`context: fork`、`hooks`。
- `allowed-tools` 语义坑：**是"本轮预授权"，不是"可用工具白名单"**——只免确认提示，其它工具照常可调；下一条用户消息后失效。要真限制得用 `disallowed-tools` 或权限规则。
- 自研成本极低：PyYAML 读 frontmatter + 目录扫描 ≈ 80 行，无需依赖。
- https://agentskills.io/specification 、https://code.claude.com/docs/en/skills.md
- MCP 侧 SEP-2640 把 skill 暴露为 `skill://` resources：**不做**，超出 14 天范围。

## 3. RAG 最小可行栈（结论：fastembed + sqlite-vec + FTS5 + 可选 rerank）
- Embedding 本地：`fastembed 0.9.1`（ONNX，不装 torch），中文 `BAAI/bge-small-zh-v1.5`（512 维 / 0.09GB / MIT）。
- 向量库：`sqlite-vec 0.1.9`，`vec0` 虚表，暴力 KNN；**有 Windows x86-64 wheel**（win_amd64，2026-03-31），不用编译。pre-v1 会 break → 锁版本。适用 ≤10 万向量。
- BM25：吃 SQLite 内置 FTS5 的 `bm25()`，零额外依赖；中文建表用 `tokenize='trigram'`（unicode61 会把整段中文当一个 token）。备选 `rank-bm25 0.2.2`（纯 Python，需自存 token）。
- Rerank：`fastembed` 的 TextCrossEncoder：`BAAI/bge-reranker-base`(1.04GB/MIT) 或 `Xenova/ms-marco-MiniLM-L-6-v2`(0.08GB)。**别引 sentence-transformers 6.2.0**（拖 torch，2GB+）。
- 融合：RRF(k=60) 合并 BM25 与向量，≈20 行，比调权重稳。
- eval：自建 30–50 条 (query, 相关 chunk id)；指标 recall@5 / MRR / nDCG@10（BEIR 口径，arXiv:2104.08663）。全量跑 <10s，可进 CI。
- 成本：检索全本地 = 0 API 费，只有生成阶段走 LLM。
- https://pypi.org/project/fastembed/ 、https://pypi.org/project/sqlite-vec/ 、https://sqlite.org/fts5.html

## 4. 多 Agent（结论：手写 supervisor，14 天更稳）
- 事实：`langgraph 1.2.18`；`langgraph-supervisor 0.0.31` 仍是 0.0.x 且硬 pin `langgraph>=1.0.2,<2`；`openai-agents 0.24.0`。
- 框架真收益是 checkpoint / 中断恢复 / HITL，这些用 SQLite 存 (state, step) 100 行也能做到。
- 代价：StateGraph/channel/reducer/compile 一套概念 + 排障要 trace；demo 阶段定位问题慢。
- 结论：自研 supervisor（路由 → 子 agent → 汇总 + 最大轮数 + 预算）≈250 行，可控好演示；LangGraph 留作 Plan B。
- 护栏必须有：**最大轮数、单次 token 预算、同工具同参数重复检测**，否则现场必死循环。
- https://pypi.org/project/langgraph-supervisor/ 、https://pypi.org/project/langgraph/

## 5. Hooks 命令协议（结论：照 Claude Code 约定抄，1 天）
- 输入：事件 JSON 走 **stdin**（HTTP hook 则是 POST body）。公共字段 `session_id`、`transcript_path`、`cwd`、`prompt_id`、`permission_mode`；工具事件另有 `tool_name`/`tool_input`/`tool_response`。
- 退出码：`0` 成功继续；`2` **阻断**（stderr 作为原因回灌模型）；其它非零 = 非阻断错误，动作继续。
- stdout 注入：exit 0 时打印 JSON → `hookSpecificOutput.additionalContext` 注入上下文；`hookSpecificOutput.permissionDecision`(allow/deny/ask) + `permissionDecisionReason` 决定放行；另有 `systemMessage`。单字段上限 **10,000 字符**。
- 超时：`timeout` 单位秒，命令 hook 默认 **600s**；`UserPromptSubmit` 降到 30s、`MessageDisplay` 10s；超时或 JSON 非法 = 非阻断错误。
- 实现要点：stdin 读完整再解析；stdout **只能**输出一个 JSON 对象，其它字符会让 JSON 失效；日志走 stderr；cwd 可能漂移（worktree/临时目录）。
- https://code.claude.com/docs/en/hooks.md
- DSH 侧同类协议 **未验证**（未逐行核实），按此约定实现即可移植。

## 6. 小时估算（112h；乐观 / 悲观）
| 模块 | 乐观 | 悲观 | 备注 |
|---|---|---|---|
| 环境 + 骨架 + 配置 | 4 | 8 | Python 版本 / 依赖 / Windows 路径 |
| MCP server + stdio client | 6 | 10 | 含超时与子进程回收 |
| Hooks（Pre/Post + 阻断） | 4 | 8 | 含 JSON schema 校验 |
| Skill 三级加载 | 4 | 7 | frontmatter + 目录扫描 |
| RAG ingest + 检索 + 融合 | 12 | 20 | 中文分词 / 切块最耗时 |
| Rerank + eval 集 | 6 | 10 | 30 条标注 |
| Supervisor 多 Agent | 10 | 18 | 路由 / 预算 / 防循环 |
| RAG demo 外壳（CLI/Web） | 8 | 14 | 演示层 |
| Harness demo 整合 | 8 | 14 | 两 demo 共用内核 |
| 联调 + 录屏 + 文档 | 8 | 14 | 最常被低估 |
| **合计** | **70** | **123** | 悲观超 11h → 必须砍 |

## 7. 八条风险与降级
1. mcp 2.x 与 v1 教程不兼容 → 锁 `mcp==2.3.0` 只读 v2 文档；降级：pin `<2` 回 v1 API。
2. sqlite-vec pre-v1 破坏性变更 / 扩展加载失败 → 锁 0.1.9；降级：numpy 暴力余弦（≤10 万条够用）。
3. FTS5 中文不分词导致 BM25 全 0 → 用 `tokenize='trigram'`；降级：jieba + rank-bm25。
4. 模型下载拖垮环境（>2GB / 公司网慢）→ 只用 fastembed ONNX；降级：换 API embedding。
5. Supervisor 死循环 / 成本失控 → 最大轮数 + 预算 + 重复检测；降级：退化为单 agent + 工具路由。
6. Hooks 污染 stdout / 超时卡住主流程 → 单 JSON、stderr 日志、自设 5s 超时；降级：hooks 只做审计不阻断。
7. 两个 demo 共用内核互相拖累 → 先冻结内核三张表（tool / skill / hook）再各写各的。
8. 演示环境不可复现（模型缓存 / 端口 / 权限）→ 全本地 + 固定 seed + 预下载模型 + 离线开关。

## 8. 自研 vs 用库
- **必须自研（否则没含金量）**：harness 内核（agent loop、tool 注册调度、Skill 三级加载、Hooks 调度与阻断）、supervisor 状态机、RAG 融合与 eval。
- **必须用库**：MCP 协议(`mcp` 2.3.0)、向量检索(`sqlite-vec`)、BM25(SQLite FTS5)、embedding/rerank(`fastembed`)、httpx / pydantic。
- **别自研**：JSON-RPC 帧、SSE/streamable HTTP、tokenizer、ONNX 推理、YAML 解析。
- 判据：协议与数值用库，**编排与策略自研**——评审看的就是后者。

## 9. 最该砍 / 最不该省
- 砍：① streamable HTTP（只留 stdio）② rerank + 自动评估（先人工看 top5）③ 多 Agent 持久化 checkpoint（内存态）。
- 省不得：① 统一 tool/skill/hook 抽象（两 demo 复用点）② 预算 / 轮数 / 超时护栏 ③ 30 条 eval 集（否则 RAG 无法自证有效）。
