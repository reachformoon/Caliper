# 工程文档

**方案定稿在**：`C:\Users\69561\Desktop\AI个人项目方案汇总.md`（v3.4，26 天 / 208h）。

本目录只放工程文档，避免与方案重复导致漂移：

- `D0-手工步骤.md` —— 装 Docker、填 key、验证
- `D0-30题清单.md` —— 评测任务集设计（30 题，含配额）
- 之后：architecture / plugin-authoring / eval-method / decisions

## 目录约定

```
src/caliper/core/       # 只放协议与数据模型（purity 检查覆盖）
src/caliper/adapters/   # SQLite / asyncio / PG / Redis 实现
scripts/                # 检查与工具
tasks/                  # 30 题 fixtures（D8 起）
tests/                  # pytest
```
