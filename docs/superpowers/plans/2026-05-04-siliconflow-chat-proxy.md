# SiliconFlow Chat Proxy & 对话入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有占星/塔罗应用中接入 SiliconFlow Chat Completions（模型 `deepseek-ai/DeepSeek-V4-Flash`，`enable_thinking=true`），通过后端代理安全调用并在前端提供“咨询对话”入口（不暴露 API Key）。

**Architecture:** 前端只请求同源 `/api/chat`；后端从环境变量读取 `SILICONFLOW_API_KEY`，用 OpenAI 兼容的 JSON 结构调用 `https://api.siliconflow.cn/v1/chat/completions`，将 `content`（可选 `reasoning_content`）透传给前端。默认不做 SSE 流式，先闭环可用性与稳定性。

**Tech Stack:** FastAPI + Pydantic v2 + Vite/React；后端 HTTP 调用使用 Python 标准库 `urllib.request`（避免引入额外依赖），带超时与错误处理。

---

## 运行前约定（不写入代码/仓库）

- 环境变量（示例）：

```bash
export SILICONFLOW_API_KEY='***'
export SILICONFLOW_MODEL='deepseek-ai/DeepSeek-V4-Flash'
export SILICONFLOW_ENABLE_THINKING='true'
```

- 说明：
  - `SILICONFLOW_API_KEY` 必填；缺失时 `/api/chat` 返回 500 且明确报错。
  - `SILICONFLOW_MODEL` 默认值为 `deepseek-ai/DeepSeek-V4-Flash`，允许覆盖。
  - `SILICONFLOW_ENABLE_THINKING` 默认 `true`，允许覆盖。

---

## Files To Touch

- Create: `services/api/app/siliconflow.py`
- Modify: `services/api/app/models.py`
- Modify: `services/api/app/main.py`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.css`

---

### Task 1: 后端 SiliconFlow 客户端封装

**Files:**
- Create: `services/api/app/siliconflow.py`

- [ ] **Step 1: 写一个最小可用的请求/响应类型（仅后端内部使用）**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class SiliconflowMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class SiliconflowChatResult:
    content: str
    reasoning_content: str | None
    raw: dict[str, Any]
```

- [ ] **Step 2: 用环境变量构造请求并调用 SiliconFlow**

实现要点：
  - 从 `os.environ` 读 `SILICONFLOW_API_KEY` / `SILICONFLOW_MODEL` / `SILICONFLOW_ENABLE_THINKING`
  - endpoint 固定：`https://api.siliconflow.cn/v1/chat/completions`
  - request body 至少包含：`model`、`messages`、`stream=false`、`enable_thinking`（按 env）
  - 使用 `urllib.request`，设置 `timeout=30`
  - 任何异常不包含 key，不打印/不记录 key

- [ ] **Step 3: 解析 response**

解析路径：
  - `choices[0].message.content`
  - `choices[0].message.reasoning_content`（可能不存在）
  - 保留 `raw` 便于排障（但不返回给前端）

- [ ] **Step 4: 自检（编译）**

Run:
```bash
python -m compileall -q services/api/app
```

- [ ] **Step 5: Commit（可选）**

```bash
git add services/api/app/siliconflow.py
git commit -m "feat(api): add siliconflow chat client"
```

---

### Task 2: 后端新增 `/api/chat`（同源代理，不暴露 key）

**Files:**
- Modify: `services/api/app/models.py`
- Modify: `services/api/app/main.py`

- [ ] **Step 1: 在 `models.py` 增加请求/响应 schema**

请求：
  - `messages`: `[{role, content}]`（OpenAI 风格）
  - `temperature` / `max_tokens` 可选（先作为透传字段）

响应：
  - `content`
  - `reasoning_content`（可选）

- [ ] **Step 2: 在 `main.py` 增加路由**

行为：
  - 校验 messages 长度（1-10）
  - 将 messages 转换后传给 `siliconflow.chat_completion(...)`
  - 若缺 key 或上游错误：返回 `HTTPException(500/502)`，detail 为稳定短码（例如 `siliconflow_not_configured` / `siliconflow_upstream_error`）

- [ ] **Step 3: 本地手工联调（curl）**

Run:
```bash
curl -sS -X POST http://localhost:5173/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [
      {"role":"system","content":"你是一个有用的助手"},
      {"role":"user","content":"用一句话解释什么是塔罗？"}
    ]
  }' | python -m json.tool
```

Expected:
  - 返回包含 `content`
  - 若开启 thinking，`reasoning_content` 可能出现

- [ ] **Step 4: Commit（可选）**

```bash
git add services/api/app/models.py services/api/app/main.py
git commit -m "feat(api): add /api/chat siliconflow proxy"
```

---

### Task 3: 前端新增“咨询对话”区块（最小闭环）

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.css`

- [ ] **Step 1: 在星盘画像输出页加入一个聊天面板**

UI 行为：
  - 一个消息列表（user/assistant）
  - 一个输入框 + 发送按钮
  - 发送时 POST `/api/chat`（同源代理）
  - 组装 messages：system prompt（包含“你是咨询师” + 当前模式说明）+ 历史对话 + 用户新消息
  - 收到返回后 append assistant message

- [ ] **Step 2: 将当前星盘画像摘要注入 system prompt（可控长度）**

策略（避免超长）：
  - 只注入：`profile.summary`、`astrology.highlights`、`astrology.interpretation` 的标题列表
  - 不注入 `raw_chart`

- [ ] **Step 3: 在塔罗细化输出页加入“追问”对话**

策略：
  - system prompt 包含：用户问题 + 抽到的牌名/正逆位 + 每张牌 meaning（不加 raw）

- [ ] **Step 4: 交互细节**

  - loading 时禁用发送
  - 出错显示在对话区上方
  - 增加“清空对话”按钮（只清前端 state）

- [ ] **Step 5: Build 校验**

Run:
```bash
cd apps/web && npm run build
```

- [ ] **Step 6: Commit（可选）**

```bash
git add apps/web/src/App.tsx apps/web/src/App.css
git commit -m "feat(web): add consultation chat panel via /api/chat"
```

---

### Task 4: 端到端体验验证（用户体验优先）

**Files:**
- None (manual)

- [ ] **Step 1: 启动服务**

```bash
cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000
cd apps/web && npm run dev -- --host 0.0.0.0 --port 5173
```

- [ ] **Step 2: 浏览器验证**

验证点：
  - 星盘画像：生成报告后能正常对话追问（至少 2 轮）
  - 塔罗细化：抽牌后能对话追问（至少 2 轮）
  - 全程无 `Failed to fetch`
  - UI 不出现 key、控制台不输出 key

- [ ] **Step 3: 故障注入**

移除 env 变量后请求 `/api/chat`：
  - 预期返回明确错误码（例如 500 + `siliconflow_not_configured`）

---

## Self-Review Checklist (for this plan)

- 覆盖了需求：后端安全代理、使用指定模型、开启 thinking、前端提供对话入口、不暴露 key。
- 无占位词（TBD/TODO），所有步骤给出了具体命令与代码形状。
- 类型一致：messages 结构在前后端一致（role/content）。

