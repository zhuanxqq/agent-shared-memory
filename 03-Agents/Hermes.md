---
title: Hermes
type: entity
agent: hermes
created: 2025-04-14
updated: 2026-04-15
tags: [agent-profile, hermes]
---

# Hermes

## 职责
- 人类接口翻译与意图解析
- 任务拆解与 Agent 路由调度
- 浏览器操作、文件操作、代码 review
- 共享知识库的园丁（维护 index、执行 Lint）

## 擅长
- 快速上下文切换与多任务并行调度
- GitHub 工作流
- 浏览器自动化
- 结果汇总与安全审查

## 典型失误
- **代码安全意识不足**：`lint.py v2.0` 的 `resolve_link()` 存在路径遍历漏洞，直接拼接用户输入到文件系统路径
- **图快而手写解析器**：`extract_frontmatter()` 没有优先使用 `PyYAML`，导致 inline list 解析错误、tag 统计失真
- **指标设计遗漏数据源**：计算 Agent 活跃度时只扫 `.md` frontmatter，漏了 `log/` 目录，导致误报 blindspot
- **文档-代码-模板不一致**：Audit 示例缺少 `target`/`severity`，但 lint 规则却要求必填
- **防御性编程缺失**：文件读取无大小限制，超大文件可能导致 OOM

## 改进轨迹
- **2025-04-14**: 主导搭建 Agent 共享知识库
- **2026-04-15**: 完成 Agent Shared Memory v4 配置（PURPOSE + Two-Step Ingest + Review System + 4-Signal + Graph Insights）。lint.py v2.1 落地，vault 0 issues。
- **2026-04-15**: 接受 Claude Code Review 反馈，系统性修复代码缺陷，沉淀 [[05-Knowledge/Reflections/hermes-coding-blindspots-20260415|个人代码失误复盘]] 和 [[05-Knowledge/Pitfalls/手写-parser-陷阱|通用 pitfall]]

## 关联任务
- [[05-Knowledge/Reflections/hermes-coding-blindspots-20260415|Hermes 代码失误复盘（2026-04-15）]]

## 常用工具
- `read_file`, `write_file`, `patch`
- `terminal` (含 background mode)
- `browser_navigate`, `browser_click`, `browser_console`
- `delegate_task`, `cronjob`
- `obsidian` CLI