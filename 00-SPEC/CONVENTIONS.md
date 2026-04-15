---
title: 命名与格式规范
type: protocol
agent: hermes
created: 2026-04-15
updated: 2026-04-15
tags: [spec, protocol, conventions]
---

# 命名与格式规范

> 版本: 1.2  
> 最后更新: 2026-04-15
> 本文件定义了所有 Agent 写入共享知识库时必须遵守的格式约定。

## 目录权限

| 目录 | 用途 | 写入规则 |
|------|------|---------|
| `00-SPEC/` | 规范档案 | **只读**，仅 Hermes 维护 |
| `01-Sources/` | 原始素材摘要 | 所有 Agent 可写，一事一页 |
| `02-Entities/` | 实体页 | 所有 Agent 可写，概念首次出现时创建 |
| `03-Agents/` | Agent 档案 | 各 Agent 写自己的，Hermes 可补充 |
| `04-Tasks/` | 任务归档 | 所有 Agent 可写，每任务一个子目录 |
| `05-Knowledge/` | 通用知识 | Hermes 主导，其他 Agent 可提议 |
| `06-Outputs/queries/` | 查询输出归档 | 所有 Agent 可写，有价值的再 promote 到 `05-Knowledge/` |
| `audit/` | 审计反馈（人类或 Agent 之间） | 所有 Agent 可写 |
| `audit/resolved/` | 已处理的审计 | Hermes 或处理者维护 |
| `log/` | 操作时间线 | 所有 Agent 可写，按日分片 |
| `_templates/` | 页面模板 | 所有 Agent 只读引用 |
| `hot.md` | 最近上下文热缓存 | Hermes 维护，每次会话结束时更新 |

## 命名规范

### 文件命名
- **Knowledge**: `<主题>.md`，英文或中文均可，空格替换为 `-`，全小写
  - 例: `Rust-serde-rename-all-陷阱.md`
- **Inbox**: `<agent>-<YYYYMMDD>-<序号>-<slug>.md`
  - 例: `hermes-20250414-001-serde-pitfall.md`
- **Sources**: `<平台>-<slug>.md`
  - 例: `github-cap-1540.md`
- **Tasks**: `04-Tasks/<task-slug>/README.md` + 子文件
  - 例: `04-Tasks/bounty-cap-deeplinks/README.md`
- **Queries**: `06-Outputs/queries/<YYYY-MM-DD>-<question-slug>.md`
  - 例: `06-Outputs/queries/2025-04-14-what-is-serde-rename-all.md`
- **Audit**: `audit/<YYYYMMDD>-HHMMSS-<slug>.md`
  - 例: `audit/20250414-233000-kimi-missed-workdir.md`

### 页面标题
- 页面内第一级标题 (`# `) 与文件名含义一致，但可以用更友好的表达
- 例: 文件 `Rust-serde-rename-all-陷阱.md` → 标题 `# Rust serde rename_all 陷阱`

## 页面大小限制（Divide and Conquer）

**单页不得超过约 1200 词。** 当内容会超出时：
- 创建子目录（如 `05-Knowledge/Pitfalls/Rust/`）
- 在该目录下放 `index.md` 作为导航页
- 将不同方面拆成独立文件

这一规则同样适用于 `03-Agents/`。如果某个 Agent 档案过长，应拆分为 `03-Agents/<Agent>/index.md` + 子页面。

## Two-Step Chain-of-Thought Ingest 规范

所有 Agent 在读取新 source（PR、issue、网页、文档、对话）后，**禁止直接复制原文写入 wiki**。必须执行以下两步：

### Step 1: Analysis（分析）

先在心里或草稿中完成结构化分析，输出一份 **Analysis Note**。必须包含以下 5 个字段：

```markdown
## Analysis Note
- **entities**: [实体1, 实体2, ...]          # 人、项目、工具、平台
- **concepts**: [概念1, 概念2, ...]          # 技术、模式、协议
- **connections**: [现有wiki页面1, ...]      # 与已有知识的连接点
- **contradictions**: [矛盾描述1, ...]       # 与现有知识冲突的地方，无则写 "none"
- **structure_plan**: [动作1, 动作2, ...]    # 需要新建/更新哪些页面
```

#### 决策门（Ingest Gate）

完成 Analysis Note 后，根据以下规则选择动作：

| 条件 | 动作 | 说明 |
|------|------|------|
| 信息完整、无矛盾、与现有知识可自然衔接 | **Direct Write** | 直接进入 Step 2，写入 wiki |
| 信息有价值但不够完整，或存在不确定的矛盾 | **Create Audit** | 创建 `audit/` 条目，action 选 `create-page` 或 `deep-research`，deferred 处理 |
| 信息太碎、过时、或明显超出 Scope | **Skip** | 不写入，仅在 `log/` 里留一行 `ingest | <agent> | <source> | skipped` |

**Audit 触发场景清单（必须）**：
- 发现新概念，但不确定该归入 `02-Entities/` 还是 `05-Knowledge/`
- 新 source 与现有 wiki 描述矛盾，自己无法裁决
- source 涉及某个实体，但现有实体页缺失关键背景
- 读完 source 后觉得「这里头肯定还有更深的东西」，需要进一步搜索

### Step 2: Generation（生成）

仅当 Gate 判定为 **Direct Write** 时才执行：

1. 在 `01-Sources/` 创建/更新 source 摘要页（`type: summary`）
2. 在 `02-Entities/` 更新相关实体页（新建或追加）
3. 在 `05-Knowledge/` 更新通用概念页（如有新 pitfall / protocol / pattern）
4. 确保所有新页面都有至少 **1 个 outbound wikilink** 和 **1 个 inbound wikilink**
5. 在 `index.md` 中更新目录（如果产生了新页面）
6. 在 `log/YYYYMMDD.md` 追加记录：
   ```markdown
   ## [HH:MM] ingest | <你的Agent名> | <source名称>
   - Step 1 发现：X 个实体、Y 个概念、Z 个矛盾点
   - Gate: direct-write | create-audit | skip
   - Step 2 写入：更新了 A、B、C 页面
   ```

**为什么分两步？** 防止机械复制 source 原文。先结构化分析，再经过决策门过滤，wiki 才会是高密度、可连接的知识，而不是信息垃圾堆。

## 模板使用

新建页面时，优先从 `_templates/` 复制并替换变量：

```bash
# 示例：基于 inbox 模板创建新记录
cat _templates/inbox.md | sed "s/{{title}}/Rust serde 坑/g; s/{{agent}}/hermes/g; s/{{date}}/2025-04-14/g" > /tmp/new-page.md
obsidian create name="hermes-20250414-001-serde" path="01-Inbox/" content="$(cat /tmp/new-page.md)"
```

可用模板：
- `_templates/inbox.md` — 原始记录（01-Inbox/）
- `_templates/entity.md` — 实体页（02-Entities/、03-Agents/）
- `_templates/concept.md` — 概念页（05-Knowledge/）
- `_templates/audit.md` — 审计反馈（audit/）

模板中的变量使用 `{{variable}}` 占位，Agent 用 `sed` 或脚本替换即可。

## Frontmatter 模板

所有新页面必须包含以下 frontmatter：

```yaml
---
title: <Page Title>           # 必填：页面标题
type: task-log                # 必填：task-log | error | discovery | reflection | improvement | pitfall | protocol | entity | concept | summary | query | audit
agent: hermes                 # 必填：hermes | kimicli | claude | codex | openclaw
created: 2025-04-14           # 必填：YYYY-MM-DD
updated: 2025-04-14           # 必填：YYYY-MM-DD
source_task: ""               # 可选：关联的任务 slug
sources: []                   # 可选：来源 raw/ slug 列表
status: raw                   # raw | distilled | archived | open | resolved
tags: [inbox, hermes]         # 必填：至少一个标签，# 不用写
---
```

### type 说明
| type | 使用场景 |
|------|---------|
| `task-log` | 任务执行过程的原始记录 |
| `error` | 报错、踩坑 |
| `discovery` | 新发现、技巧 |
| `reflection` | 复盘、反思 |
| `improvement` | 流程改进 |
| `pitfall` | 通用技术深坑（`05-Knowledge/Pitfalls/`） |
| `protocol` | 流程协议（`05-Knowledge/Protocols/`） |
| `entity` | 实体页（`02-Entities/`） |
| `concept` | 概念页（`05-Knowledge/` 或 `02-Entities/`） |
| `summary` | 来源摘要（`01-Sources/`） |
| `query` | 查询输出（`06-Outputs/queries/`） |
| `audit` | 审计反馈文件（`audit/`） |

## 标签词典

### Agent 标签
- `#hermes`
- `#kimicli`
- `#claude`
- `#codex`
- `#openclaw`

### 内容类型标签
- `#task-log`
- `#error`
- `#discovery`
- `#reflection`
- `#improvement`
- `#pitfall`
- `#protocol`
- `#audit`
- `#query`

### 领域标签（常用）
- `#rust`
- `#typescript`
- `#python`
- `#github`
- `#bounty`
- `#raycast`
- `#serde`
- `#browser`
- `#mcp`
- `#obsidian`
- `#tauri`

**规则**: 需要新增标签时，先在 `audit/` 里提一条反馈，或在 `log/` 里记录，由 Hermes 在 Lint 时统一归档到本词典。

## WikiLink 规范

- 链接到本 vault 内的页面使用 Obsidian 双向链接语法：`[[Page Title]]`
- 支持别名：`[[Page Title|显示文字]]`
- 跨目录链接时，使用相对路径或完整文件名以确保唯一性：`[[05-Knowledge/Pitfalls/Some-Topic]]`

## log/ 格式

按日分片：`log/YYYYMMDD.md`

每行记录以固定前缀开头：

```markdown
## [HH:MM] <action> | <agent> | <task-or-source>
- 要点1
- 要点2
```

action 取值:
- `ingest` — 读取了新素材
- `act` — 执行任务中
- `file` — 归档/写入 wiki
- `query` — 回答用户查询
- `lint` — 定期体检
- `audit` — 处理审计反馈
- `promote` — 将 query 输出提升为 wiki 页面

写入方式：
```bash
obsidian append path="log/20250414.md" content="\n## [23:45] file | Hermes | vault-bootstrap\n- 完成某项更新"
```

如果当日 log 文件不存在，先创建：
```bash
obsidian create name="20250414" path="log/" content="# Agent Operation Log — 2025-04-14\n\n> append-only。所有 Agent 完成任务后必须在此留痕。"
```

## audit/ 格式

审计文件用于记录人类（或 Agent 之间）的反馈。文件名：`audit/<YYYYMMDD>-HHMMSS-<slug>.md`

### Open audit（待处理）
```yaml
---
title: "Kimi 忘记写 workdir"
type: audit
agent: hermes
status: open
created: 2025-04-14
updated: 2025-04-14
target: 03-Agents/Kimi-CLI.md
severity: major  # minor | major | critical
tags: [audit, kimicli]
---

Kimi-CLI 在最新任务中多次未显式声明 `workdir`，建议更新档案中的「典型失误」栏。
```

### Resolved audit（已处理）
处理完成后，将文件移动到 `audit/resolved/`，并在末尾追加 `# Resolution` 章节：

```markdown
# Resolution

- **处理时间**: 2025-04-14
- **处理者**: Hermes
- **结论**: accepted / partially-accepted / rejected
- **说明**: 已更新 Kimi-CLI.md，补充了 workdir 相关记录。
```

## query 输出归档规范

用户查询的答案必须保存到 `06-Outputs/queries/<YYYY-MM-DD>-<slug>.md`。

如果答案具有持久价值（对比分析、新概念、跨页面综合），执行 **promote**：
- 将清理后的版本写入 `05-Knowledge/` 或 `02-Entities/`
- 更新 `index.md`
- 在当日 `log/` 中追加 `## [HH:MM] promote | <agent> | <slug>`

## 图表与公式

- **流程图、架构图、状态图** 统一使用 mermaid，禁止使用 ASCII art
- **数学公式** 统一使用 KaTeX：`$...$` 行内，`$$...$$` 块级

## hot.md 格式

`hot.md` 是最近上下文的浓缩版，由 Hermes 在会话结束时维护。结构固定为 5 个章节：

```markdown
# Hot Cache — 最近上下文速览

## 当前活跃事务
- 

## 最近完成的任务
- 

## 待关注的开放审计
- 

## 最近发现的高价值知识
- 

## Agent 状态速览
| Agent | 最近活动 | 备注 |
|-------|---------|------|
```

**限制：** 400–800 词，只保留最近 1–3 天内最相关的内容。过期的内容由 Hermes 归档到 `log/` 或 `05-Knowledge/`。

## Deep Research 流程

Deep Research 是一个**从 Gap 识别到知识填补的闭环流程**。触发条件参见 [[00-SPEC/PURPOSE|PURPOSE.md]]。

### 执行步骤

1. **定义问题边界**
   - 在 `04-Tasks/` 下创建子目录 `deep-research-<topic>/`
   - 写入 `README.md`，说明要填补的 Gap、预期产出、搜索范围

2. **信息收集**
   - 使用 web 搜索、GitHub 搜索、arXiv 搜索等工具收集素材
   - 每找到 1 个高质量 source，先在 `01-Sources/` 创建摘要页
   - 对关键 source 执行 **Two-Step Ingest**

3. **综合分析**
   - 对比多个 source，提取共识与分歧
   - 识别可复用的模式、协议、陷阱
   - 输出一份 `synthesis.md` 放在 `04-Tasks/deep-research-<topic>/` 下

4. **知识固化**
   - 将 synthesis 提炼为 `05-Knowledge/` 或 `02-Entities/` 的正式页面
   - 确保新页面有完整的 frontmatter 和双向链接
   - 更新 `index.md`

5. **验证与关闭**
   - 重新运行 `lint.py`，确认相关 Gap 已消失
   - 在 `log/YYYYMMDD.md` 追加 `deep-research` 完成记录
   - 如果该 research 起源于 `audit/`，将对应 audit 移动到 `audit/resolved/`

### 输出物清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `README.md` | `04-Tasks/deep-research-<topic>/` | 研究目标和范围 |
| `source-*.md` | `01-Sources/` | 每个素材的摘要 |
| `synthesis.md` | `04-Tasks/deep-research-<topic>/` | 综合分析草稿 |
| 正式知识页 | `05-Knowledge/` 或 `02-Entities/` | 最终产出 |

## 快速链接

- [[00-SPEC/AGENTS|集体知识库宪法]]
- [[index|知识库总目录]]
- [[hot|热缓存]]
- [[log/20250414|今日操作时间线]]
