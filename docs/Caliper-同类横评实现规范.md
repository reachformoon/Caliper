# Caliper · 同类横评实现规范（第 3 周 / v0.4）

> 定位：与《AI个人项目方案汇总》v3 的**附录 B** 配套，回答「不同 harness 跑同一套题，怎么实现才不算自说自话」。
> 边界：只比**同域 coding harness**（文件读写 + shell + 隐藏测试），必须能无头运行；不评模型，不做排行榜。
> 日期：2026-10-31 起草，实施窗口 2026-11-17 → 11-23。

---

## 0. 目标与可宣称范围

| 可以宣称 | 不可以宣称 |
|---|---|
| 某 harness 在本套题上的 pass-rate（带 95% CI） | 总排名、「更好」 |
| 两两差值 Δ 与 CI；能否区分（tier） | 「因为它的 RAG 更好」这类机制归因 |
| $/task、wall-clock、工具调用数的比值 | 跨域结论（研究型 agent 比编码 agent） |
| 失败类型分布、成本-质量 Pareto | 无 n、无预算、无环境说明的孤立数字 |

**因果强度**：横评是**观察性比较**（多变量同时变），只有 14 天的「自身对照」才是单变量因果。报告里必须写这句话。

---

## 1. 组件图

```
tasks/ + hidden_tests/        bench-spec.json（预注册）
        │                              │
        ▼                              ▼
┌───────────────┐   materialize   ┌──────────────────┐
│  Runner       │───────────────► │  per-run worktree │
│ (矩阵/重试/超时)│                 │  env / HOME / cwd │
└──────┬────────┘                 └────────┬─────────┘
       │ invoke(task, ws, budget)          │
       ▼                                   ▼
┌───────────────┐   全部请求走本地代理   ┌──────────────┐
│ HarnessAdapter│──────────────────────►│ cal proxy    │──► 上游模型
│ lithe/bare/..│                        │ pin/计数/限额 │
└──────┬────────┘                        └──────┬───────┘
       │ RunResult + artifact                  │ usage.jsonl
       ▼                                       ▼
┌───────────────┐    隐藏测试挂载后执行    ┌──────────────┐
│  Judge        │──────────────────────►│ runs.jsonl    │
└───────────────┘                        └──────┬───────┘
                                                ▼
                                   stats → metrics / pairwise / report / Pareto
```

**一句话**：适配器只负责「怎么跑」，判分器负责「跑得怎样」，代理负责「花了多少」——三者解耦，才能换 harness 而不换尺子。

---

## 2. 适配器协议

### 2.1 协议

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

@dataclass
class Budget:
    max_steps: int = 40
    max_tokens: int = 200_000
    max_wall_s: int = 600
    max_usd: float = 0.50

@dataclass
class RunResult:
    harness: str; task_id: str; seed: int
    ok: bool                  # 进程是否正常结束（不代表通过）
    wall_s: float
    tokens_in: int; tokens_out: int
    tool_calls: int
    cost_usd: float
    failure: str | None       # timeout|crash|budget|tool_error|no_artifact
    meta: dict = field(default_factory=dict)

class HarnessAdapter(Protocol):
    name: str
    def healthcheck(self) -> tuple[bool, str]: ...
    def invoke(self, task, ws: Path, budget: Budget, run_id: str) -> RunResult: ...
```

### 2.2 三类实现

| 类型 | 例子 | 实现方式 | 成本可测 |
|---|---|---|---|
| in-process | `lithe`、`bare` | 直接 import，调用内核 loop | ✅ 精确（代理计数） |
| CLI subprocess | `aider`、Claude Code、DSH | 命令模板 + 环境变量 + 超时 + 进程组 kill | ✅ 走代理则精确；自带订阅则估算 |
| replay | 任意 | 读 cassette 回放，CI 用 | ✅ 0 |

### 2.3 准入条件（缺一不进横评）

1. 能无头调用（一条命令跑完，无需人工确认）；
2. 具备文件读写 + shell 能力（否则不是同类）；
3. 模型可配置到同一端点（或至少同模型家族；否则只能进「参考组」，不进严格比较）；
4. 行为可重复（固定 temperature/seed；不接受纯随机）；
5. 许可证允许公开基准对比。

不满足的先记入 `missing.json`（写原因），**不许静默丢弃**。

---

## 3. 任务契约与隐藏测试

字段（与 14 天 gate 共用 schema）：

```yaml
id: fix-circular-import
prompt: "..."                  # 对双方一致，不含测试命令
fixtures: fixtures/repo-a/     # 初始工作区
hidden_tests: tests-h/         # 运行时才挂载，双方都看不到
test_cmd: "pytest -q tests-h"
subtests: [t_import, t_cycle, t_cli]
budget: {max_steps: 30, max_wall_s: 420}
tags: [bugfix, cross-file]
```

**任务体检（开跑前必做，否则整套数据作废）**：
- 空解（原样不动）→ **必须失败**（题不是已解决）；
- 参考补丁 → **必须通过**（题可解）；
- 隐藏测试在挂载前对 harness 不可见（防止对着测试写代码）。

---

## 4. 环境隔离（无容器方案）

宿主没有 Docker，所以用「拷贝 + 进程边界 + 代理」三件套：

| 风险 | 措施 |
|---|---|
| 污染仓库 | 每次 `copytree` 到临时目录；父仓 hash 前后比对，变了就标 `contaminated` |
| 串味 HOME/缓存 | 覆盖 `HOME`、`XDG_*`、`TMPDIR` 到 run 目录；清 `PYTHONPATH`；sanitize `PATH` |
| 孤儿进程 | POSIX `start_new_session=True`，Windows `CREATE_NEW_PROCESS_GROUP`；超时整组 kill，再扫残留 PID |
| 网络失控 | 统一设 `HTTP(S)_PROXY=http://127.0.0.1:9`（死端口）；允许白名单时显式放行；**报告披露「非 syscall 级强制」** |
| 越界写盘 | 运行后扫描 worktree 之外的 mtime，异常记 `out_of_tree` |

可选：宿主装了 Docker 时，`--isolate docker` 走容器；两套隔离必须产出同一 schema。

---

## 5. 预算与模型网关（横评公平性的核心）

**所有 harness 的模型请求都指向本地代理**（OpenAI 兼容，`/v1/chat/completions`，支持 stream 透传）：

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
export OPENAI_API_KEY=caliper-run-<run_id>     # 代理按 key 归属到 run
```

代理职责：

1. **pin 模型**：忽略客户端 model 字段，映射到 `bench-spec.json` 指定的版本；
2. **计数**：从响应 `usage` 累加 token，写 `usage.jsonl`（按 run_id）；
3. **限额**：超 token / 超 $ 立即 402，并把 `failure=budget` 写回；
4. **录制**：请求/响应落 cassette，供审计与 replay；
5. **审计**：记录实际生效的 temperature、max_tokens，发现客户端偷偷改参数就标 `param_drift`。

**例外**：自带订阅、无法改 base_url 的 harness（如某些 Claude Code 模式）→ 只能估算 token，报告里单列「成本不可比」，且**不参与 $/task 排名**。

---

## 6. 判分

- **主指标**：`pass_rate = 通过子测试数 / 子测试总数`（0–1 连续量）。
- **副指标**：`binary = 全部子测试通过`（0/1，用于"完全解决率"）。
- 判分器只读 worktree，不读 harness 自报结果；**默认不用 LLM-judge**（避免判分方差），若要 rubric 分，单列为「辅助」。
- 失败分类枚举：`timeout | crash | budget | tool_error | patch_conflict | no_artifact | contaminated`。

---

## 7. 统计口径

| 项 | 方法 |
|---|---|
| 单 harness pass-rate | Wilson 95% CI（小 n 比正态近似稳） |
| 两两差值 Δ | 按任务配对，bootstrap 重抽任务 10k 次 → 95% CI |
| 能否区分 | `|Δ| ≥ MDE` 且 CI 不含 0 → 才说"有差异" |
| 分层（tier） | 按点估计排序，相邻两者若 CI 重叠或 `|Δ| < MDE` 则同层 |
| 多重比较 | 3 个 harness = 3 对；用 Holm 校正，或全部标"探索性" |
| MDE（n=30，二值） | ≈ 25pp 才能区分；通过率判分 + 配对可压到 10–20pp |
| 种子 | 主实验 1 seed × 30 题；10 题 × 3 seeds 估计方差 |

**预注册**：开跑前把题集、指标、阈值、适配器版本写进 `bench-spec.json` 并 hash；报告里贴 hash，跑完不许改口径。

---

## 8. 数据与报告

```
results/<run-id>/
  bench-spec.json        # 预注册 + sha256
  runs.jsonl             # 每行 = harness × task × seed
  usage.jsonl            # 代理侧 token/成本
  metrics.csv            # 每 harness 汇总（pass_rate, CI, $/task, wall, tool_calls）
  pairwise.csv           # 每对：Δ、CI、MDE、可区分否
  report.md              # 表格 + Pareto + 失败分布 + 限制
  missing.json           # 没跑起来的 harness 与原因
  reproduce.py           # 一条命令重算指标
```

**报告必须包含**：CI、MDE、失败分布、公平性偏离（如订阅制计费不可比）、以及与 14 天 gate 的口径差异说明。

**呈现方式**：成本-质量 Pareto 图 + 分层表（Tier A/B/C），**不放单一分数排行榜**。

---

## 9. 失败模式与处置

| 现象 | 处置 |
|---|---|
| harness 装不上 / 要登录 | 记 `missing.json`，报告写"未参与"，不补数据 |
| 只有交互模式 | 尝试 `--message`/`exec` 无头；不行就退出横评 |
| 超时留孤儿 | 进程组 kill + PID 扫描；结果标 `timeout` |
| 成本打不住 | 代理硬限额；单 run 上限 $0.5，整轮 $50 |
| 结果不可复现 | 固定 seed/temperature；报告方差；必要时降为"pilot" |
| 改到 worktree 外 | 前后 hash 比对，标 `contaminated` 并剔除 |

---

## 10. 实施步骤（D15–D21）

| D | 内容 | 验收 |
|---|---|---|
| 15 | 协议 + 本地代理 + `bare` adapter | `cal bench run --adapter bare` 跑通 3 题，token 计数准确 |
| 16 | `aider` adapter + 隔离/超时/进程组 | 10 题冒烟，0 孤儿进程 |
| 17 | 30 题 × 3 harness 全量跑批 | 90 run 落盘，缺失有原因 |
| 18 | 补跑 + 第 4 adapter（可选）+ 失败分类 | `missing.json` 完整 |
| 19 | 统计：CI / MDE / tier / Pareto | 指标可一条命令重算 |
| 20 | 报告 + 数据发布 + 长文 | 含上述披露项 |
| 21 | v0.4.0 发布 + 复盘 | 陌生环境可复现 |

**完成判据**：任一第三方按 `reproduce.py` 能从 `runs.jsonl` 重算全部指标；报告的每个"有差异"结论都能定位到 CI 与 MDE。

---

## 11. 已知限制（照抄进报告）

1. 无容器 → 网络与环境隔离是"尽力而为"，非 syscall 级强制。
2. n=30 → 只能区分大差距；小差距一律写"无法区分"。
3. 订阅制 harness 的成本不可比，只能比 pass-rate。
4. 只覆盖 coding 任务；不含多轮对话、长周期任务、人机协作。
5. 一个模型、一个温度：结论不外推到其他模型。
