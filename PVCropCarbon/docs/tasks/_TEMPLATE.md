# T-YYYY-MM-DD-<slug>：<任务名>

status: draft            <!-- draft | ready | running | done | blocked -->
类型: 工程任务（非实验）

一个任务一个文件。Claude Code 起草 → 用户批准 → Codex 执行并在下方「执行记录」填写。

---

## 目标

<要 Codex 做的一件具体工程事：建环境 / 改脚本 / 修数据问题 / 出某张独立图。>

## 交付物

- `<路径>` —— <说明>

## 步骤

1.

## 验收（可判定）

- [ ]

## 失败即停（写 BLOCKED，不要自行决定）

-

## 备注

<Codex 不读聊天记录，需要的上下文都写这里。>

---

## 执行记录（Codex）

commit: `<短哈希>`  ·  起止: `<…>`

- 装了什么 / 改了什么（含精确版本、SHA256）
- 验收结果逐条
- BLOCKED / 异常
- 给 Claude Code 的问题
