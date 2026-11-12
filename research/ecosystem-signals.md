# 2026-10 社区生态信号（采集截至 2026-10-30 Asia/Shanghai）

口径：只记录能点开的一手/可核验来源并附发布日期；查不到确切值的写"约/未验证"。总量类数字取自 GitHub 页面快照或公开数据集，会随时间变动。

## 结论先行
2026 上半年起，编码 Agent 从"工具"变成"平台"：内核（harness）+ 三层扩展面（Skill / Plugin / Hook）+ 两个协议（MCP 出工具、ACP/A2A 出协作）已经成型。要讲的"轻量化、可扩展 harness"就是这套分层本身，不是造词。

## ① Harness 内核层：有学术解剖，也有硬数据
| 信号 | 关键事实 | 日期 | 来源 |
|---|---|---|---|
| 学科化 | "harness engineering" 2026 年初被命名；11 个生产级 harness 源码解剖（Claude Code、Codex CLI、Gemini CLI、OpenHands、Aider、Mini-SWE-Agent、Hermes、Pi、OpenCode、OpenClaw、Mistral Vibe，外加元 harness Omnigent），归纳 7 大子系统、29 个复用模式、18 条建议、90 行最小可用 harness | 2026-07-15 提交 | https://arxiv.org/abs/2609.00006 |
| 反直觉结论 | 约 400 万行 Python/TS/Rust：没有任何 runtime 引入通用 agent 框架；没有一个用向量嵌入检索代码；skills 采用率 9/11 高于 MCP 8/11；ACP 已进 6 个系统，并出现 "harness hosting" 第三角色 | 同上 | 同上 |
| 体量参照 | openclaw 393,064 stars（全站第 6）；opencode 221,584（周增 +5,921）；claude-code 148,352（周增 +1,493） | 2026-10-26 / 09-28 | https://news.qiniu.com/archives/1792990305728 ; https://news.qiniu.com/archives/1790560170841 |
| 轻量内核 | 已有"小内核"实现（harness-kernel：small TypeScript kernel for app-owned runtimes）；DSH 自身是 Cordis 插件化 SDK，能力按 Service Definition / Provider / Consumer 三角色拆包 | 2026 | https://github.com/Ducks-Software-AI-Infrastructure/harness-kernel ; https://deepseek-harness.github.io/deepseek-harness/develop/practice/index.md |

## ② Agent Skills：已进标准组织，事实标准成立
| 信号 | 关键事实 | 日期 | 来源 |
|---|---|---|---|
| AAIF 收编 | Anthropic 把 Agent Skills 捐给 Linux Foundation 下的 Agentic AI Foundation（AAIF），连同名称/logo/GitHub org/agentskills.io 域名；Anthropic+Google+OpenAI 等工程师以个人身份维护，Lead Maintainers：David Soria Parra、Mahesh Murag | 2026-10-22 | https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation |
| 生态规模 | 70+ agent 平台已支持（ChatGPT、Cursor、GitHub Copilot、VS Code 等）；标准 2025-12 发布；约 100 万 skills 上架、近 2.8 亿次安装（skills.sh，7 个月） | 2026-10-22 | https://aaif.io/blog/agent-skills-sharing-team-expertise-across-ai-agents |
| AAIF 盘子 | 项目 3 → 10（2025-12 起步）：MCP、A2A、Agent Router、agentgateway、AGENTS.md、goose，新增 Agent Skills（Anthropic）、Open Responses（OpenAI）、OpenEnv（Hugging Face）、OpenSandbox（Alibaba）；于 AGNTCon+MCPCon NA 2026-10-22/23 圣何塞发布 | 2026-10-22 | https://aaif.io/news/agentic-ai-foundation-announces-four-new-projects |
| SKILL.md 格式 | 目录 = SKILL.md + 可选 scripts/ references/ assets/；frontmatter：name ≤64（小写+连字符）、description ≤1024、license、compatibility ≤500、metadata、allowed-tools（实验）；渐进式加载；规范 Apache-2.0 / CC-BY-4.0 | 2026 | https://agentskills.io/specification |
| 生态质量 | 结构普查：347,382 skills / 71,430 subagents / 20,212 plugins / 6,324 marketplaces；9.70% 加载失败（skill 7.89%、subagent 21.94%、plugin 0.16%），主因 frontmatter 坏（38,183 例） | 2026-08-14 抓取 | https://zenodo.org/records/21936490 |
| 头部 skill | cloudflare/security-audit-skill 47,178 stars（周增 15,072，当周全站飙星第一）；6 阶段：侦察→覆盖分配→独立验证→结构化输出→复核→中立报告 | 2026-10-26 | https://news.qiniu.com/archives/1792990305728 |

## ③ MCP：2026-07-28 是唯一大版本，方向"无状态 + 扩展化"
| 变化 | 要点 | 来源 |
|---|---|---|
| 无状态化 | 删除 initialize/initialized 握手与 Mcp-Session-Id；每请求在 _meta 带 protocolVersion/clientCapabilities/clientInfo；版本不匹配返回 UnsupportedProtocolVersionError（SEP-2575） | https://modelcontextprotocol.io/specification/2026-07-28/changelog |
| 发现与订阅 | 新增必实现 RPC server/discover；HTTP GET + resources/subscribe/unsubscribe 被 subscriptions/listen（单条长活 POST 流）取代 | 同上 |
| 多轮请求 | MRTR：服务端返回 resultType:"input_required" + inputRequests，客户端带 inputResponses 重试；取代服务端主动发 roots/sampling/elicitation（SEP-2322） | 同上 |
| 瘦身 | 移除 ping、logging/setLevel、notifications/roots/list_changed、SSE 重放（Last-Event-ID）；日志级别改到 _meta | 同上 |
| 扩展框架 | Tasks/MCP Apps 从 core 移出为带版本扩展；Client/Server Capabilities 增 extensions 字段 | 同上 ; https://aaif.io/blog/mcp-2026-changes-the-rules（2026-09-03） |
| 缓存/可观测 | 列表类结果必须带 ttlMs + cacheScope；tools/list 需确定性排序以提 prompt cache 命中；_meta 定义 OTel traceparent/tracestate/baggage（SEP-2549 / SEP-414） | 同上 |
| 生态规模 | 官方 registry 38,977 个 server（快照 2026-10-04，ProtocolProbe 数据集，CC-BY-4.0）；awesome-mcp-servers 94,487 stars | https://zenodo.org/records/23386800 ; https://news.qiniu.com/archives/1788747048975 |
| 安全事件 | CSA 研究简报：2026-05-04「MCP security crisis」、2026-07-01「tool poisoning 与 IDE 自动执行」、2026-09-02「Deadbugz：运行时门控的 MCP 元数据投毒供应链攻击」（详情页被 Cloudflare 拦截，未验证） | https://labs.cloudsecurityalliance.org/research/csa-research-note-deadbugz-mcp-metadata-poisoning-20260902-c/ |

## ④ Plugin / Marketplace：分发层与协议层解耦
| 形态 | 事实 | 日期 | 来源 |
|---|---|---|---|
| Claude Code 插件 | plugin manifest + marketplace 索引；生态 20,212 plugins / 6,324 marketplaces（同上普查）；官方知识工作插件包 anthropics/knowledge-work-plugins 33,029 stars（周增 +2,790）、anthropics/financial-services 37,865 | 2026-10-26 | https://news.qiniu.com/archives/1792990305728 |
| 进程内插件 mod | 插件可用 JS 在宿主进程注册函数型 hook（mods），与命令型 hook 并存 | 2026 | https://code.claude.com/docs/en/hooks.md |
| DSH 插件市场 | 市场 = 纯 JSON 索引（format:1）；插件源为 npm 或 git（commit + path）；engines.dsh 做兼容筛选；索引 ≤128 MiB、图标可内联 base64；DSH 不内置索引源，只校验格式、不背书内容 | 2026 | https://deepseek-harness.github.io/deepseek-harness/guide/plugin-market.md |
| 内容包规模 | ECC 类"流程插件包"：68 agents / 292 skills / 94 commands，累计 268,440 stars | 2026-09-28 | https://news.qiniu.com/archives/1790560170841 |

## ⑤ Hooks：两条可对比的工程路线
| 维度 | Claude Code（跨进程 JSON 协议） | DeepSeek Harness / Cordis（进程内事件） |
|---|---|---|
| 事件点 | 33 个：SessionStart/Setup/UserPromptSubmit/UserPromptExpansion/PreToolUse/PermissionRequest/PermissionDenied/PostToolUse/PostToolUseFailure/PostToolBatch/Notification/MessageDisplay/SubagentStart/SubagentStop/TaskCreated/TaskCompleted/Stop/StopFailure/TeammateIdle/InstructionsLoaded/ConfigChange/CwdChanged/DirectoryAdded/FileChanged/WorktreeCreate/WorktreeRemove/PreCompact/PostCompact/PreModelSwitch/PostModelSwitch/Elicitation/ElicitationResult/SessionEnd | agent/pre-step、agent/request、agent/request-error、agent/turn-stopping、system-prompt/assemble、llm/stream、tools/result、session/event |
| 处理器 | command（stdin JSON）/ http（POST body）/ mcp_tool / prompt / subagent；字段 type、if（单条权限规则）、timeout、statusMessage、once、async、asyncRewake、shell、onFailure | ctx.on(...) 注册，插件卸载自动移除；四种模式 emit/bail/serial/waterfall，waterfall 必须调 next()，不调即拦截 |
| 输入 / 阻断 | stdin 字段：session_id、prompt_id、transcript_path、cwd、scratchpad_dir、permission_mode、hook_event_name、tool_name、tool_input、tool_use_id；exit 0 放行、2 阻断、其他非阻断 | 监听器返回值即结果；bail/serial 首个非空返回值短路；waterfall 可包装下游返回值、改写入参与输出 |
| 持久化 | transcript.jsonl + 事件 JSON 输出字段（continue/stopReason/systemMessage 等） | 持久事实在 session/event：turn/*、step/*、tool/call、tool/result、compaction/*；实时控制在 agent/* |
| 取舍 | 跨语言、可审计、可阻断，代价是每事件一次进程启动 | 零 IPC、可改状态、类型安全，代价是同语言同进程 |
来源：https://code.claude.com/docs/en/hooks.md ; https://deepseek-harness.github.io/deepseek-harness/develop/framework/events.md ; https://deepseek-harness.github.io/deepseek-harness/reference/agent-lifecycle.md

## ⑥ RAG 2026：从"检索管道"转向"上下文编排"
| 信号 | 结论 | 日期 | 来源 |
|---|---|---|---|
| 范式之争有实证 | ACL 2026 Industry：Enhanced RAG vs Agentic RAG 在性能与成本上的权衡——agentic 不等于更优，取决于场景与预算 | 2026-07 | https://aclanthology.org/2026.acl-industry.5/ |
| 反向证据 | 11 个编码 harness 无一用向量嵌入检索代码，代码场景靠 grep/AST/图谱等确定性检索 | 2026-07-15 | https://arxiv.org/abs/2609.00006 |
| 工艺演进 | contextual retrieval（先补文档级上下文再嵌入）仍是 2026 主流做法；late chunking 继续演进（图感知分块等） | 2026-03（据 arXiv ID 推断） | https://arxiv.org/pdf/2603.22633 |
| 评测 | 排序仍用 Recall / nDCG@k（常见 nDCG@5 为主口径），生成侧单列；工程侧需另报延迟与 token 成本 | 2026 | https://aclanthology.org/2026.semeval-1.447.pdf |
| 产品面 | Tencent/WeKnora：RAG + 推理 Agent + 自维护 Wiki，30,621 stars | 2026-09-28 | https://news.qiniu.com/archives/1790560170841 |
| 代码知识图谱 | Graphify：本地 AST 建图，文档/PDF 语义检索可外调模型；135,394 stars（周增 +6,903） | 2026-10-26 | https://news.qiniu.com/archives/1792990305728 |

## ⑦ 多 Agent 组织：三种形态都还活着，成本是分水岭
| 形态 | 现状证据 | 来源 |
|---|---|---|
| 图 / 状态机（supervisor） | LangGraph：厂商称 20 万+ 生产应用量级（LangChain State of Agent Engineering 2026，数字未独立验证） | https://zenodo.org/records/19109057（转引 langchain.com） |
| 对话式多 Agent | AutoGen → 开源 AG2 + Azure AI Agent Service，以 Azure 存量客户为主 | 同上 |
| 角色制 Crew | CrewAI 在内容/研究/客服流水线扩散 | 同上 |
| 成本红线 | 编排层占生产推理成本 15–40%（arXiv 2601.13671）；错选框架可致 2–4× 推理成本 | 同上 |
| 组织化产品 | Paperclip 89,994 stars：给 Agent 团队设组织架构、预算、审批（"OpenClaw 是员工，Paperclip 是公司"）；Orca 106,018：每 Agent 一个 git worktree 并行 + 集中评审 | https://news.qiniu.com/archives/1790560170841 ; https://news.qiniu.com/archives/1792990305728 |
| 跨 Agent 协议 | A2A 已归 AAIF；ACP 在 6 个 harness 落地并带 harness hosting 角色 | https://aaif.io/news/agentic-ai-foundation-announces-four-new-projects |

## 选题映射：2 个 demo 覆盖六件事（建议）
| demo | 主题锚点 | RAG | 多 Agent | MCP | Skill | Plugin | Hooks |
|---|---|---|---|---|---|---|---|
| A | 轻量 harness 内核（可加载/可卸载能力） | 混合检索 + contextual 预处理，报 recall@k / nDCG@5 | supervisor + 顺序流水线（不做自由辩论） | 无状态 MCP client，支持 2026-07-28 | SKILL.md 加载器 + 校验（防 9.7% 结构失败） | 插件 manifest + 本地索引市场 | 进程内事件总线（pre-step / tool-result） |
| B | 组织层：任务编排与审计 | 检索即工具（agentic retrieval），带成本日志 | 组织架构 + 预算/审批（Paperclip 式） | MCP server 侧：暴露检索/工单工具 | 把流程固化成 skill 包并版本化 | 分发：npx skills add 式安装 | 命令型 hook 做审计与阻断（exit 2 语义） |

## 可作为简历叙事的 5 条硬信号
1. **Skills 是事实标准**：AAIF 2026-10-22 收编 + 70 平台 + 约 100 万 skills/2.8 亿安装；会写合规 SKILL.md（name/description 约束、渐进加载）是可验证工程能力。
2. **轻量内核有学术背书**：arXiv 2609.00006 给出 7 子系统、29 模式与 90 行最小 harness，"薄内核 + 插件 seam"是可引用设计而非造词。
3. **MCP 唯一大版本变更**：2026-07-28 无状态化（去 session、server/discover、MRTR、extensions），做"支持 2026-07-28 MCP"即证明跟进最新协议。
4. **Hooks 双路线可对比**：命令型 33 事件 JSON 协议 vs 进程内 Cordis 事件（bail/waterfall），方案里写清取舍而非堆功能。
5. **生态数字可量化**：38,977 MCP servers、20,212 plugins、347,382 skills、9.70% 结构失败率——足以支撑"加载前校验 + 权限分级"的设计叙事。

## 未验证 / 需二次确认
- CSA 三份 MCP 安全简报的具体 CVE 与影响面（页面 403，仅取标题与日期）。
- skills.sh 的"约 100 万 / 2.8 亿"为 Anthropic/AAIF 自述口径，无第三方复核。
- LangGraph "20 万+ 生产应用"来自厂商调研，未独立验证。
- DSH 的事件名（agent/*、session/event）在官方文档中未以 "hooks" 作为品牌词，术语需按 DSH 文档表述。
