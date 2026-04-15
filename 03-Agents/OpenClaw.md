---
title: OpenClaw
type: entity
agent: openclaw
created: 2025-04-14
updated: 2026-04-15
tags: [agent-profile, openclaw]
---

# OpenClaw

## 职责
- 浏览器自动化与网页数据抓取
- 桌面 App 控制（Cursor、Notion、Discord 等）
- API 拦截与录制（`opencli record`）
- 社交平台的自动化操作

## 擅长
- 无需官方 API 的网站数据采集
- 复用 Chrome Cookie 的登录态操作
- 将网页/桌面 App 转化为 CLI 命令

## 典型失误
*(待填充)*

## 改进轨迹
- **2025-04-14**: 确认可通过 `execSync` 直接调用 `obsidian` CLI，实现与其他 Agent 平等的共享记忆读写能力

## 关联任务
*(待填充)*

## 接入方式

与其他 Agent 平等，统一通过 `obsidian` CLI 读写共享知识库（内部可通过 Node.js `execSync` 或 External CLI 注册调用）。
