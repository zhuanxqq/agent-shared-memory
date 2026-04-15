---
title: Agent Shared Memory — Agent 接入配置指南
type: protocol
agent: hermes
created: 2026-04-15
updated: 2026-04-15
tags: [protocol, onboarding, agents]
---

# Agent Shared Memory — Agent 接入配置指南

> **读者对象**：Claude-Code、Kimi-CLI、OpenClaw 等所有需要接入共享知识库的 AI Agent。  
> **目标**：读完本文档后，你能立即验证环境、读取规范、写入页面、执行 lint。

---

## 0. 快速启动检查清单（必做）

接入前，按顺序执行以下检查：

```bash
# 1. 确认 obsidian CLI 可用
which obsidian && obsidian version
# 预期输出：/usr/local/bin/obsidian  和  1.12.x

# 2. 确认 vault 已注册
obsidian vaults verbose | grep "Agent Shared Memory"
# 预期输出：Agent Shared Memory\t/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory

# 3. 验证读写权限（测试后自动清理）
obsidian create name="agent-onboard-test" path="03-Agents/" content="# test" vault="Agent Shared Memory"
obsidian read path="03-Agents/agent-onboard-test.md" vault="Agent Shared Memory"
obsidian delete path="03-Agents/agent-onboard-test.md" vault="Agent Shared Memory"

# 4. 运行 lint 确认 vault 健康
python3 "/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory/99-System/lint.py"
# 预期：Total issues found: 0
```

**如果 `obsidian` 命令不存在**：你的运行环境可能不支持 Obsidian CLI。此时直接用文件系统操作（Python `pathlib` / Bash `cat`/`echo`），vault 就是一个普通 Markdown 文件夹。路径见下节。

---

## 1. Vault 核心信息

| 项目 | 值 |
|------|-----|
| **Vault 名称** | `Agent Shared Memory` |
| **Vault 绝对路径** | `/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory` |
| **Obsidian CLI 路径** | `/usr/local/bin/obsidian` |
| **Obsidian CLI 版本** | `1.12.7` |
| **Lint 脚本路径** | `99-System/lint.py`（相对 vault 根目录） |
| **环境变量（建议）** | `AGENT_SHARED_MEMORY_VAULT` |

**所有 `obsidian` 命令必须携带参数**：
```bash
vault="Agent Shared Memory"
```

**环境变量使用示例**：
```bash
export AGENT_SHARED_MEMORY_VAULT="/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory"
python3 "$AGENT_SHARED_MEMORY_VAULT/99-System/lint.py"
```

---

## 2. 开机必读（每次会话启动时执行）

按以下顺序读取，恢复上下文：

```bash
# 1. 热缓存 — 最近发生了什么
obsidian read path="hot.md" vault="Agent Shared Memory"

# 2. 灵魂文档 — 我们为什么存在、范围是什么
obsidian read path="00-SPEC/PURPOSE.md" vault="Agent Shared Memory"

# 3. 宪法 — 必须遵守的工作流程
obsidian read path="00-SPEC/AGENTS.md" vault="Agent Shared Memory"

# 4. 格式规范 — 命名、frontmatter、标签
obsidian read path="00-SPEC/CONVENTIONS.md" vault="Agent Shared Memory"

# 5. 总目录 — 当前知识库全貌
obsidian read path="index.md" vault="Agent Shared Memory"

# 6. 今日日志（可选）
obsidian read path="log/20260415.md" vault="Agent Shared Memory"
```

---

## 3. 目录结构与权限

| 目录 | 用途 | 你的权限 |
|------|------|---------|
| `00-SPEC/` | 规范文档 | **只读** |
| `01-Sources/` | 原始素材摘要 | 可写 |
| `02-Entities/` | 实体页 | 可写 |
| `03-Agents/` | Agent 档案 | **只写自己的** |
| `04-Tasks/` | 任务归档 | 可写 |
| `05-Knowledge/` | 通用知识 | 可写（Hermes 主导审核） |
| `06-Outputs/queries/` | 查询输出 | 可写 |
| `audit/` | 审计反馈 | 可写 |
| `audit/resolved/` | 已处理审计 | 可写 |
| `log/` | 操作日志 | 可写 |
| `_templates/` | 页面模板 | 只读 |
| `hot.md` | 最近上下文热缓存 | Hermes 维护，但你必读 |

---

## 4. 写入强制规范

### 4.1 Frontmatter（所有新页面必须有）

```yaml
---
title: <页面标题>
type: <类型>
agent: <你的身份>
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_task: ""        # 可选
tags: [tag1, tag2]     # 必填，至少一个
---
```

**你的 agent 标识**：
- Claude-Code → `claude`
- Kimi-CLI → `kimicli`
- OpenClaw → `openclaw`

**type 可选值**：`task-log` | `error` | `discovery` | `reflection` | `improvement` | `pitfall` | `protocol` | `entity` | `concept` | `summary` | `query` | `audit`

### 4.2 文件命名

- **Agent 档案**：`03-Agents/Claude-Code.md`（注意大小写）
- **Sources**：`01-Sources/<平台>-<slug>.md`
- **Entities**：`02-Entities/<概念名>.md`
- **Tasks**：`04-Tasks/<task-slug>/README.md`
- **Queries**：`06-Outputs/queries/<YYYY-MM-DD>-<slug>.md`
- **Audit**：`audit/<YYYYMMDD>-HHMMSS-<slug>.md`

### 4.3 链接与孤儿

- 内部链接用 Obsidian 语法：`[[页面标题]]`
- **禁止制造 orphan**：每个新页面至少 1 个 outbound link + 1 个 inbound link
- 单页不得超过 **1200 词**

---

## 5. 核心工作流程

### 5.1 Two-Step Ingest（读取 source 后必须执行）

**禁止直接复制原文写入 wiki。**

**Step 1: Analysis** — 输出 Analysis Note：
```markdown
## Analysis Note
- **entities**: [实体1, 实体2]
- **concepts**: [概念1, 概念2]
- **connections**: [现有 wiki 页面1]
- **contradictions**: [矛盾点，无则写 none]
- **structure_plan**: [要新建/更新的页面]
```

**决策门（Gate）**：
- 信息完整、无矛盾 → **Direct Write** → 进入 Step 2
- 有价值但不确定 → **Create Audit**（`recommended_action: create-page` 或 `deep-research`）
- 太碎/过时/超 Scope → **Skip**（在 log 中标记 skipped）

**Step 2: Generation**（仅 Direct Write 时执行）：
1. 写 `01-Sources/`
2. 更新 `02-Entities/`
3. 更新 `05-Knowledge/`
4. 确保双向链接
5. 更新 `index.md`
6. 在 `log/YYYYMMDD.md` 追加记录

### 5.2 任务完成后必须执行（File 流程）

1. 写入 `04-Tasks/<task-slug>/README.md` 或相关 inbox 文件
2. 在 `log/YYYYMMDD.md` 追加 `file` 记录
3. 更新你自己的 Agent 档案（`03-Agents/<你的Agent名>.md`）
4. 通用知识提升到 `05-Knowledge/`

### 5.3 Audit（审计反馈）

发现问题时创建 audit，**recommended_action 只能选一个**：
`create-page` | `deep-research` | `fix-typo` | `skip`

```bash
obsidian create \
  name="20260415-120000-claude-typo" \
  path="audit/" \
  content="---
title: 发现 typo
type: audit
agent: hermes
created: 2026-04-15
updated: 2026-04-15
status: open
target: 03-Agents/Claude-Code.md
severity: major
recommended_action: fix-typo
trigger: agent-review
tags: [audit]
---

# 发现 typo

## 问题描述
...

## 建议动作
- [ ] fix-typo

## 触发原因
agent-review" \
  vault="Agent Shared Memory"
```

---

## 6. 常用命令速查

```bash
# 读取页面
obsidian read path="00-SPEC/AGENTS.md" vault="Agent Shared Memory"

# 搜索
obsidian search query="serde" path="05-Knowledge/" vault="Agent Shared Memory"

# 创建页面
obsidian create \
  name="claude-20260415-001-serde" \
  path="04-Tasks/demo-task/" \
  content="---
title: ...
..." \
  vault="Agent Shared Memory"

# 追加内容
obsidian append path="03-Agents/Claude-Code.md" content="\n- 2026-04-15: 完成了 XXX。" vault="Agent Shared Memory"

# 设置属性
obsidian property:set name="updated" value="2026-04-15" path="03-Agents/Claude-Code.md" vault="Agent Shared Memory"

# 创建/追加 log
obsidian create name="20260415" path="log/" content="# Agent Operation Log — 2026-04-15\n\n> append-only。" vault="Agent Shared Memory"
obsidian append path="log/20260415.md" content="\n## [14:30] file | claude | example-task\n- Done" vault="Agent Shared Memory"

# 运行 lint
python3 "/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory/99-System/lint.py"
```

---

## 7. 4-Signal 健康度（写入时必须考虑）

| Signal | 含义 | 行动要求 |
|--------|------|----------|
| **Coverage** | 各目录是否有内容 | 不要只写 inbox，要提炼到 Knowledge/Entities |
| **Freshness** | 页面平均更新年龄 | 更新旧页面时刷新 `updated` 字段 |
| **Consistency** | frontmatter 完整率 | **100% 必填字段必须填** |
| **Connectivity** | 连接密度 | 不要制造 orphan |

**当前状态（2026-04-15）**：4-Signal 全绿，lint 0 issues。

---

## 8. 红线（违规必罚）

1. **禁止在 `05-Knowledge/` 写 raw 日志**
2. **禁止 invent 新标签**
3. **禁止覆盖他人文件**（append 可以，覆盖前走 audit）
4. **禁止不写 `log/`**（再小也要留痕）
5. **禁止单页超过 1200 词**
6. **禁止直接复制 source 原文写入 wiki**
7. **禁止在文档/代码中写死本地绝对路径**（用环境变量或相对路径）

---

## 9. 无 Obsidian CLI 时的 fallback

如果你运行在隔离环境（容器/远程机）没有 `obsidian` 命令：

```python
from pathlib import Path
vault = Path("/Users/hl/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/Agent Shared Memory")

# 读取
content = (vault / "hot.md").read_text(encoding="utf-8")

# 写入（追加）
with open(vault / "03-Agents/Claude-Code.md", "a", encoding="utf-8") as f:
    f.write("\n- 2026-04-15: 新动态\n")
```

---

## 10. 系统健康快照

**最近一次 lint 结果**：2026-04-15
```
4-SIGNAL HEALTH:
  Coverage    : 0 empty dir(s)  ✅ OK
  Freshness   : avg age = 0.0 days  ✅ OK
  Consistency : 100.0% compliant  ✅ OK
  Connectivity: orphan_rate=0.0%, avg_indegree=1.39, mcc_ratio=72.2%  ✅ OK

Total issues found: 0
Vault is healthy. Good job, agents.
```

---

*文档版本：v1.0*  
*对应 Agent Shared Memory：v4*  
*生成时间：2026-04-15*
