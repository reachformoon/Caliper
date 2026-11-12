# Caliper · 定稿 Brief

> 产品名：**Caliper**（CLI：`cal`）　定稿：2026-10-29　开工：2026-11-03
> 一句话：**一个所有能力默认关闭、必须先在真实任务集上证明自己才允许进入默认配置的 coding agent harness。**
> 本文件是 v3 产品方案的收敛版；逐日细节以本文件为准。

---

## 1. 两个项目（一个产品，两种交付）

```
Caliper = 可恢复运行时 (Runtime) + 单写多读编排 (Orchestrator)
        + 混合检索 (Retrieval) + 证据闸门 (Gate)
```

| | **项目 1：Caliper Gate**（第 1–2 周） | **项目 2：Caliper Core**（第 3–4 周） |
|---|---|---|
| 身份 | **仪器**：评测、对照、判定、台账 | **机器**：内核、编排、检索 |
| 回答的问题 | "这个能力值不值？" | "任务怎么才能不崩、不失控、可追溯？" |
| 交付 | 闸门 CLI + 能力台账 + 私有任务集 + 双向用例 | 可恢复运行时 + 编排层 + 检索服务 |
| 版本 | v0.1 能跑 → v0.2 能证明 | v0.3 不崩 → v0.4 能检索 |
| 复用关系 | 产出的 runner / trace schema 被项目 2 直接复用 | 产出的两个能力（编排、检索）被项目 1 的判据验收，产出台账 v2 |

**为什么是这两个**：JD 里出现频率最高的两组词，一组是 *eval / ablation / trace replay / cost attribution*（→ Gate），另一组是 *checkpoint 恢复 / 沙箱 / sub-agent 编排 / 观测*（→ Core）。两者咬合后得到的句子，是"我既造了尺子，也造了被测的机器"。

---

## 2. 技术架构

### 2.1 项目 2（Core）的运行时分栈

```
cal (CLI) ── run / resume / trace / cap / bench
   │
   ├── RUNTIME ──────── 事件日志(append-only) · checkpoint/resume · 幂等去重
   │                    权限门(deny/confirm) · 沙箱(进程组+cgroup+禁网) · span 树 · 成本归因
   ├── ORCHESTRATOR ─── 单写多读 · 独立消息通道 · 每 agent 预算 · 级联取消 · 结果对账
   ├── RETRIEVAL ────── hybrid(BM25+dense) · rerank · 增量索引 · 陈旧检测 · 以工具暴露
   ├── HOOKS ────────── 可执行护栏（PreToolUse / 完成前自检）· 双向用例
   └── CONTEXT ──────── 预算分配 · 压缩 · 超限裁剪 · 压缩后规则保留率
```

| 模块 | 默认 | 关键实现 | 失败模式 | 怎么被证明 |
|---|---|---|---|---|
| Runtime | 常开 | SQLite 五类事件 + step 级快照 + idempotency key | 恢复后重复副作用 | 故障演练 MTTR |
| Orchestrator | **OFF** | reader 池 + 结构化结果协议 + 级联取消 | 成本爆炸、对账失败 | 三拓扑对照 |
| Retrieval | **OFF** | 增量索引 + 版本戳 + hybrid/rerank | 索引过期、噪声注入 | recall@k + token 税 |
| Hooks | 部分 ON | 可执行脚本，非散文规则 | 越收越紧勒死 agent | 双向用例 |
| Context | 常开 | 确定性注入优先 | 静默丢约束 | 规则保留率 |

### 2.2 项目 1（Gate）的五层流水线

```
任务集 ──▶ 执行器 ──▶ 采集 ──▶ 判定 ──▶ 台账
40 私有题   矩阵 runner   trace/   三类口径    capability
+ T-Bench2   3 seeds     SQLite   性能/安全/成本  ledger.md
      ▲                                    │
      └──────── CI 回归门禁 ◀───────────────┘
```

- **任务集**：40 题（≥10 道跨文件/文档题，专供检索类能力）+ Terminal-Bench 2.0 子集；每题 6 字段，镜像 digest 冻结。
- **执行器**：能力 × seeds × 任务矩阵，能力通过 `capabilities/*.yaml` 注册，进/出配置不改代码。
- **采集**：每步 prompt/tool/args/result/token/延迟 + `parent_agent_id`（这是能算"哪个 sub-agent 最贵"的前提）。
- **判定**：性能型看 Δsuccess 的 CI 下界；安全型看拦截率/误报；成本型看 cost 比值。
- **台账**：`ledger.md` 六行，每行一个带区间的数字 + verdict（KEEP / REJECTED / KEEP(safety)）。

### 2.3 多 Agent 的具体设计（项目 2 实现、项目 1 测量）

**三种拓扑**（对照组必须存在，否则只是复读炒作）
- **A 单 Agent**（基线）
- **B orchestrator + 2–3 readers**（单写多读，预期赢家）
- **C 并行写手 swarm**（预期反例：重复劳动 + 合并冲突）

**四条硬约束**（这是"懂多 Agent"的证据，不是装饰）
1. **独立消息通道**：reader 之间不共享上下文，只回传结构化 JSON（找到什么/在哪/置信度）。
2. **每 agent 独立预算**：token/步数/墙钟三上限，超限即取消；orchestrator 死 → 全部级联取消。
3. **职责分区**：reader 按文件/目录认领，杜绝重复劳动。
4. **结果对账**：orchestrator 必须显式处理冲突结论，并计数。

**指标**：成功率、token/task、墙钟、$/task、**重复劳动率**、**对账冲突数**、**上下文串味事件数**。

### 2.4 RAG 的具体设计（项目 2 实现、项目 1 测量）

**三配置**：R0 无检索（ripgrep 当工具）/ R1 dense top-k / R2 hybrid(BM25+dense) + cross-encoder rerank。

**两语料分开测**（结论价值全在这里）：代码语料（预期 grep 赢符号查找）、文档/ADR/工单语料（预期 hybrid 赢）。

**四指标**：端到端成功率、recall@k/precision/MRR（自建 80 条 QA 对）、**token 税**（检索结果占多少上下文）、**索引过期**（改文件后陈旧检测延迟 + 故障注入：agent 会不会用旧结果）。

### 2.5 自进化长期记忆：做哪一半、不做哪一半

| 层 | 做什么 | 状态 |
|---|---|---|
| **能力自演化**（真自进化） | trace 挖掘 → 提出候选能力 → 闸门判定 → 进/退；模型升级后自动重测，掉阈值自动降级（治理 harness rot） | **v0.2 起做**（Gate 的核心机制） |
| **结构化事实记忆** | 仓库约定、失败模式库、用户偏好，存 SQLite 三元组 + 带失效与污染检测，按需注入 | **v0.5 可选**（2 周） |
| **"记忆 = 向量召回"** | 把历史对话塞进向量库自动召回 | **明确不做**：被批为 memo, not true memory；且是当前最大的噪声源 |
| 记忆的评测 | 有/无记忆的成功率差、注入污染后的退化幅度 | v0.5 由 Gate 验收 |

---

## 3. 项目 1：Caliper Gate（第 1–2 周，8h/天）

### 第 1 周：把尺子造出来

| Day | 任务 | 完成判据 |
|---|---|---|
| D1 | 执行器骨架：接 Terminal-Bench 2.0 + Docker 沙箱，跑通 1 题出分 | `cal bench run --task 1` 出 0/1 |
| D2 | 私有集 40 题（≥10 道跨文件/文档），6 字段 + digest 冻结 | tasks.jsonl + git tag |
| D3 | trace 采集：每步 prompt/tool/args/result/token/延迟 | 单任务完整 trace |
| D4 | 存储 + 指标 schema（含 parent_agent_id） | 能查"某个 sub-agent 的 token" |
| D5 | 统计：任务级 bootstrap CI + seeds 方差分解 | 输出 point[lo,hi] |
| D6 | 双向用例 60 条（该拦/该放） | 放宽规则 → 测试变红 |
| D7 | 基线：40 题 × 1 配置 × 3 seeds | baseline 带 CI，Go/No-Go |

### 第 2 周：证明三个能力都"不值得默认开"

| Day | 任务 | 完成判据 |
|---|---|---|
| D8 | 能力注册（`capabilities/*.yaml`）+ 矩阵 runner | 一行配置切能力 |
| D9 | 闸门判定三类口径 + 台账生成器 | `cal gate report` 出台账 |
| D10 | C1 长规则集 vs 极简 prompt | 台账第 1 行 |
| D11 | C2 延迟加载工具（成本型） | 台账第 2 行（token 降多少） |
| D12 | C3 完成前自检中间件 | 台账第 3 行 |
| D13 | 全矩阵复跑 + leave-one-out | ≥1 条 null result |
| D14 | README 首屏 = 台账、`docs/rejected.md`、v0.2 tag | 可对外展示 |

**验收**：5 类产物齐（runner / 任务集 / 双向用例 / 台账 / 拒绝清单）；≥1 条 null result；台账号称全部带 95% CI；CI 一键跑。

---

## 4. 项目 2：Caliper Core（第 3–4 周，8h/天）

### 第 3 周：让它不崩、不失控

| Day | 任务 | 完成判据 |
|---|---|---|
| D15 | 事件日志五类（session/step/tool_call/decision/checkpoint） | 可回放读取 |
| D16 | checkpoint/resume（step 快照：上下文/工具态/文件 diff） | kill -9 后续跑 |
| D17 | 幂等去重（idempotency key） | 恢复不重复写文件 |
| D18 | 沙箱：进程组 + cgroup 限额 + 目录隔离 + 默认禁网 | 死循环被回收 |
| D19 | 权限门（deny/confirm）+ 复用 Gate 的双向用例 | 60 用例绿 |
| D20 | 故障演练四场景（kill -9/断网/超时/磁盘满） | MTTR 表 |
| D21 | **C4 编排**：reader 池 + 独立通道 + 预算 + 级联取消 + 对账 | 8 路并发零串味 |

### 第 4 周：能检索、能归因、能发布

| Day | 任务 | 完成判据 |
|---|---|---|
| D22 | span 树（session→agent→step→tool）+ trace 重放 | 能答"这步为何慢" |
| D23 | 成本归因到层（prompt/tool/retry/agent） | 单任务成本分解 |
| D24 | **C5 检索**：索引构建 + hybrid + rerank + 工具暴露 | p95 < 300ms |
| D25 | 增量索引 + 陈旧检测 + 过期故障注入 | 改文件 5s 内可检测 |
| D26 | 用 Gate 跑 C4/C5 的对照（三拓扑 + 三配置） | **台账 v2** |
| D27 | README + asciinema（60s：kill -9 → resume）+ 博客 | 可发布 |
| D28 | v0.4 tag + 缓冲 + 联合报告 | 收尾 |

**验收**：kill -9 后 ≤30s 恢复且副作用不重复（自动化测试）；8 路 reader 零串味、预算与级联取消生效；检索 p95<300ms、陈旧索引可检测；任一步可归因 token；台账 v2 包含 C4/C5 的裁决。

---

## 5. 四周总路线

| 周 | 版本 | 主题 | 关键 Demo |
|---|---|---|---|
| W1 | v0.1 | 能跑（执行器 + 基线） | `cal bench run` 出分 |
| W2 | v0.2 | 能证明（闸门 + 台账 v1） | `gate` 拒绝一个能力 |
| W3 | v0.3 | 不崩（恢复 + 沙箱 + 编排） | kill -9 续跑；8 路 reader |
| W4 | v0.4 | 能检索（检索 + 归因 + 发布） | 台账 v2 全绿/全红对照 |

**可选第 5–6 周**：v0.5 结构化事实记忆（自进化长期记忆的"做的那一半"）+ 上下文压缩策略对照。

---

## 6. 最终交付物清单

1. 可安装 CLI（`cal`，8 条子命令）+ `pipx install` 指引
2. README 首屏 = 能力台账（六行，≥3 行 REJECTED）
3. `docs/rejected.md`：做过的、被自己否掉的能力与数据
4. 60 秒 asciinema（崩溃恢复 + 闸门拒绝）
5. 45 天版本历史（v0.1→v0.4，台账变化）
6. 两篇博客：①"我如何证明多 Agent 只值 4 个点" ②"RAG 在代码上输给 grep，但在文档上赢了 6 个点"

---

## 7. 风险与砍法

| 风险 | 应对 |
|---|---|
| 4 周做不完 | 按序砍：C5 只做文档语料 → 私有集 40→25 → 编排退化为 2 readers → 检索降级为"工具 + 离线评测" |
| 数字不好看 | **照发**。负结果是这个产品唯一的护城河 |
| 手痒想做 Web UI / 云服务 | 禁止。形态就是 CLI |
| 手痒想做通用框架 | 禁止。只做 coding 场景 |

---

## 8. 非功能需求（NFR）

> 轻量 / 快 / 可扩展不是形容词，是必须在 CI 里被测量的数字。这一节把它们钉死。

### 8.1 硬指标

| 属性 | 指标 | 目标 | 测量方式 |
|---|---|---|---|
| 轻量 | 单二进制体积 | ≤ 25MB | `go build -ldflags="-s -w"` 后 `ls -lh` |
| 轻量 | 常驻内存（默认配置，不含嵌入模型） | ≤ 150MB | 跑 30 步任务，`/usr/bin/time -v` 看峰值 RSS |
| 轻量 | CLI 冷启动 | ≤ 80ms | `hyperfine 'cal --help'` |
| 快 | 内核开销（不含模型与工具执行） | **p95 ≤ 20ms/步** | step 内埋时间戳，导出到 trace |
| 快 | 权限判定 | ≤ 1ms | 微基准（预编译规则集） |
| 快 | 事件写入 | p99 ≤ 2ms | 批量 + WAL，压测 10k 事件 |
| 快 | 检索延迟（含 rerank） | p95 ≤ 300ms | 80 条 QA 压测 |
| 快 | 检索缓存命中 | ≤ 50ms | 同一查询二跑 |
| 快 | 增量索引 | ≤ 5s（中型仓库） | 改 1 文件 → 重建 |
| 可扩展 | 新增能力改动量 | **1 个 yaml + 1 个接口实现，内核 0 改动** | code review 规则 |
| 可扩展 | Gate 结果缓存命中率 | ≥ 70% | 复跑矩阵统计 |
| 可扩展 | 能力加载方式 | 进程外（可执行 / 目录），禁止 in-process plugin | 架构约定 |

### 8.2 实现约束（守住这些数字的唯一办法）

1. **热路径零治理**：日志批量 + WAL 异步刷盘；trace 异步写；hook 规则**预编译**、命中才 spawn；checkpoint **只在有写操作后**做。
2. **不用 CGO**；嵌入模型与 reranker 可选且**懒加载**，默认关闭——要不要开由台账决定，不由手感决定。
3. **能力一律进程外**：内核只认协议，不 import 任何能力代码。代价是每次调用多一次序列化（2–5ms），换来主程序永不因插件崩溃。
4. **事件 schema 带 version**，升级走迁移脚本（没有这一步，v0.3 之后会寸步难行）。
5. **Gate 自身要可扩展**：输入哈希缓存 + 增量重跑 + 分层抽样（10 题粗筛 → 40 题确认）。没有这层，第 5 个能力就会让你放弃所有实验。

### 8.3 冲突与取舍（写清楚，避免临时妥协）

| 冲突 | 取舍 |
|---|---|
| 轻量 vs 检索质量 | 默认不加载嵌入模型；要质量就显式开能力，并把成本记进台账 |
| 快 vs 可观测 | trace 全量落盘但异步；强一致只发生在 checkpoint |
| 扩展 vs 快 | 进程外能力多一次序列化，接受 |
| 扩展 vs 轻 | **拒绝**多租户、分布式、Web UI；一旦要做，"轻量"立即作废 |

### 8.4 每条 NFR 都必须有对应测试（进 CI，超阈值即失败）

- `bench/kernel_overhead_test.go` —— 内核 p95 ≤ 20ms
- `bench/cold_start.sh` —— hyperfine 冷启动 ≤ 80ms
- `bench/permission_micro_test.go` —— 权限判定 ≤ 1ms
- `bench/retrieval_latency_test.go` —— p95 ≤ 300ms / 缓存 ≤ 50ms
- `bench/gate_cache_test.go` —— 缓存命中率 ≥ 70%
- `test/resume_idempotency_test.go` —— kill -9 后 ≤30s 恢复且副作用不重复

