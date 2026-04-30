# AI 辅助开发日常操作指南

本项目已经接入三层 AI 工作流：

- Trellis：`.trellis/` 管理项目规范、任务 PRD、开发日志和交接记录。
- Magic Context：`magic-context.jsonc` 与 `.contextignore` 管理跨会话记忆、压缩和高信号上下文。
- Oh-My-OpenCode-Slim：`opencode.jsonc`、`.opencode/oh-my-opencode-slim.jsonc` 和 `.opencode/commands/` 管理多智能体调度与工作流命令。

高优先级上下文入口是 `.opencode/context-priority.md`。每次 AI 开发会话都应先加载它，再读取当前任务 PRD 和相关 Trellis spec。

## 0. 一次性环境准备

在机器上安装/启用这些工具后再进入项目根目录使用：

```powershell
npm install -g @mindfoldhq/trellis@beta
bunx --bun @cortexkit/opencode-magic-context@latest setup
bunx oh-my-opencode-slim@latest install
opencode auth login
opencode models --refresh
```

如果只想检查 Magic Context 配置：

```powershell
bunx --bun @cortexkit/opencode-magic-context@latest doctor
```

## 1. 如何新建一个需求任务

推荐用 Trellis 脚本创建任务目录：

```powershell
python .trellis/scripts/task.py create "打印预览页面最后调整" --slug 04-30-print-preview-final
```

然后编辑生成的：

```text
.trellis/tasks/04-30-print-preview-final/prd.md
```

如果要手工创建，可复制：

```text
.trellis/tasks/TEMPLATE.md
```

任务 PRD 至少写清楚：

- 问题和目标
- 非目标，避免 AI 扩大范围
- 涉及桌面端、后端、前端、数据或文档的哪一层
- 验收标准
- 需要运行的检查命令

## 2. 如何唤醒 AI Agent 开始写代码并关联记忆

从项目根目录启动 OpenCode：

```powershell
opencode
```

在 OpenCode 内执行：

```text
/start-task 04-30-print-preview-final
```

这个命令会要求 Agent 优先读取：

- `AGENTS.md`
- `.opencode/context-priority.md`
- `.trellis/spec/loop-calculator/`
- 当前任务的 `prd.md` / `task.json` / `implement.jsonl` / `check.jsonl`
- `.trellis/workspace/` 中相关历史日志

Magic Context 会负责跨会话记忆和历史压缩；`.contextignore` 会排除 `node_modules`、`.git`、构建产物、日志、缓存和二进制表格文件。

如果任务涉及后端 API、SQLite、服务层或数据导入，Agent 还会加载：

```text
.trellis/spec/backend/index.md
.trellis/spec/backend/*.md
```

如果任务涉及跨层数据流或重复模式，Agent 会加载：

```text
.trellis/spec/guides/index.md
```

## 3. 阶段性结束后如何保存记忆和更新状态

在 OpenCode 内执行：

```text
/save-session 04-30-print-preview-final
```

保存时应记录：

- 本次进展
- 修改过的文件
- 遇到的坑
- 已运行的验证命令和结果
- 下次继续时的第一步

重要经验应写入：

```text
.trellis/spec/loop-calculator/
```

普通过程记录应写入：

```text
.trellis/workspace/<developer>/journal-N.md
```

任务状态、验收标准变化和交接说明应写回：

```text
.trellis/tasks/<task-slug>/prd.md
```

如果只是想让 AI 保存当前进度，不需要提交代码，可以直接说：

```text
请运行 /save-session <task-slug>，只更新 Trellis 日志和任务状态，不提交。
```

## 4. 可用的 Agent 工作流动作

| 动作 | 入口 | 用途 |
|------|------|------|
| start-task | `/start-task <task-slug>` | 读取任务 PRD、项目规范、Magic Context 规则和相关历史日志 |
| save-session | `/save-session <task-slug>` | 汇总当前进展，更新任务状态，写入 workspace journal |
| manual memory | 直接要求“保存为长期记忆” | 将反复使用的项目约定提升为 Magic Context memory 或 Trellis spec |

## 5. 本项目的默认上下文纪律

- 先读 `AGENTS.md`，再读 Trellis spec。
- UI-only 任务不改计算/后端逻辑。
- 计算、电流、电压降、线缆推荐或设备聚合逻辑变化必须补测试。
- 数据合并/去重变化前先读 `数据库合并去重机制.md`。
- 不碰无关的 dirty worktree 文件。
- 结束前运行最小有意义检查；不能运行时记录准确失败原因。
