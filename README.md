# SleepMind — AI 睡眠优化 Agent

> LangGraph + ReAct + RAG + Function Calling + Redis + FastAPI + React + IoT Mock

## 快速启动

### 1. 创建 PostgreSQL 数据库

```sql
CREATE DATABASE sleepmind;
```

### 2. 安装依赖

```bash
cd e:\Sleep_Consultant\backend
pip install -r requirements.txt
```

### 3. 配置 API Key（可选）

编辑 `backend/.env`：
```
OPENAI_API_KEY=你的AIHubMix-API-Key
```
> 无 Key 时使用 Mock LLM，可正常运行。

### 4. 一键初始化

```bash
python scripts/init_project.py
```

### 5. 启动后端

```bash
uvicorn main:app --reload --port 8000
```

### 6. 启动前端

```bash
cd e:\Sleep_Consultant\frontend
npm run dev
```

**API 文档**：http://localhost:8000/docs
**前端**：http://localhost:5173

---

## 项目结构

```
Sleep_Consultant/
├── backend/
│   ├── main.py                       # FastAPI 入口 (v0.2.0)
│   ├── core/config.py                # 配置管理（AIHubMix LLM）
│   ├── models/sleep_session.py       # Pydantic Schema
│   ├── data/
│   │   ├── parser.py                 # CSV → SleepSession
│   │   └── metrics.py                # 睡眠指标计算（AASM 对照）
│   ├── db/
│   │   ├── database.py               # SQLAlchemy 异步引擎
│   │   ├── orm_models.py             # ORM 表定义
│   │   └── crud.py                   # CRUD + 7日趋势
│   ├── rag/
│   │   ├── embedder.py               # 向量化（AIHubMix 代理）
│   │   ├── ingest.py                 # 知识库入库脚本
│   │   └── retriever.py              # ChromaDB 检索
│   ├── agent/
│   │   ├── state.py                  # LangGraph AgentState
│   │   ├── graph.py                  # 状态图（5节点+条件路由）
│   │   └── nodes/
│   │       ├── input_parser.py       # 节点1：数据解析
│   │       ├── memory_retrieval.py   # 节点2：记忆+RAG检索
│   │       ├── react_agent.py        # 节点3：CoT 5步推理
│   │       ├── action_executor.py    # 节点4：IoT 执行
│   │       └── memory_updater.py     # 节点5：记忆写回
│   ├── memory/
│   │   ├── redis_store.py            # Redis 短期记忆（24h TTL）
│   │   ├── episodic.py               # PostgreSQL 情节记忆
│   │   ├── semantic.py               # ChromaDB 语义画像
│   │   ├── summarizer.py             # LLM 周度记忆压缩
│   │   └── manager.py                # 三层记忆统一入口
│   ├── iot/
│   │   ├── ac_controller.py          # Mock 空调控制器
│   │   ├── calendar_client.py        # Mock 日历客户端
│   │   └── scheduler.py              # APScheduler 定时任务
│   ├── mcp_server/
│   │   └── tools.py                  # MCP 工具注册（6个工具）
│   ├── api/routes/
│   │   ├── sleep.py                  # 上传 + 历史
│   │   ├── agent.py                  # Agent SSE 分析
│   │   └── iot.py                    # IoT 执行 + 记忆压缩
│   ├── scripts/init_project.py       # 一键初始化
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx                   # 路由 + 导航（5页面）
│       ├── api.js                    # Axios API 封装
│       ├── index.css                 # 暗色主题 CSS
│       ├── pages/
│       │   ├── Dashboard.jsx         # 评分卡+时间线+趋势图
│       │   ├── UploadPage.jsx        # 拖拽上传+指标展示
│       │   ├── AnalysisPage.jsx      # SSE Agent 推理展示
│       │   ├── HistoryPage.jsx       # 历史记录+趋势图
│       │   └── IotPanel.jsx          # IoT 控制面板
│       └── components/
│           ├── SleepTimeline.jsx     # Recharts 甘特图
│           └── ScoreCard.jsx         # 评分卡组件
├── knowledge_base/
│   └── sleep_guidelines.md           # 睡眠医学知识
└── chroma_db/                        # ChromaDB 向量库（自动创建）
```

---

## API 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload-sleep` | 上传 CSV 睡眠数据 |
| GET | `/api/history/{user_id}` | 获取历史记录 |
| GET | `/api/record/{record_id}` | 获取单条记录详情 |
| GET | `/api/analyze/stream` | SSE 流式 Agent 分析 |
| POST | `/api/analyze` | 非流式分析 |
| POST | `/api/execute/ac-schedule` | 下发空调温控计划 |
| POST | `/api/execute/calendar` | 创建日历提醒 |
| POST | `/api/execute/calendar/auto` | 自动生成日历提醒 |
| GET | `/api/iot/history` | IoT 执行历史 |
| POST | `/api/memory/compress` | 触发记忆压缩 |

## LangGraph Agent 流程

```
START → input_parser → memory_retrieval → react_agent
  → [有IoT动作?] → action_executor → memory_updater → END
                └─ [无动作] ──→ memory_updater → END
```
