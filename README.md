# 无为AI (Wuwei-AI)

面向中老年用户的方言语音聊天 AI。名字取自道家"无为而治"，寓意让老人与 AI 的对话如同与家人闲聊一般自然——不需要学习新技能，不需要适应普通话。

## 核心特性

- 语音优先交互：按住说话，自动回复
- 方言支持：MVP 支持普通话、粤语、四川话，架构可扩展更多方言
- 适老化设计：大字体、大按钮、高对比度 UI，语速可调
- 国产大模型：基于通义千问 (Qwen) LLM
- 温暖人格：耐心、体贴、口语化，像贴心晚辈

## 技术栈

- **后端**: Python 3.11 + FastAPI + Uvicorn
- **前端**: Gradio 4.x (挂载在 FastAPI 内)
- **数据库**: SQLite (SQLModel ORM)
- **LLM**: 通义千问 (Qwen) - 阿里云 DashScope
- **语音**: 科大讯飞 ASR/TTS (方言支持)
- **部署**: Docker + Docker Compose

## 项目结构

```
wuwei-ai/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/v1/              # API 路由
│   ├── speech/              # 语音管道 (ASR/TTS/Pipeline)
│   ├── dialect/             # 方言引擎 (适配器注册表)
│   ├── chat/                # 对话引擎 (LLM/Memory/Prompt)
│   ├── db/                  # 数据层 (Models/Repositories)
│   └── ui/                  # Gradio 适老化 UI
├── tests/                   # 单元测试 + 集成测试
├── scripts/                 # 运维脚本
├── docs/                    # 设计文档
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
pip install uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 API 密钥
```

需要准备的密钥：
- **通义千问 API Key**: https://dashscope.console.aliyun.com/
- **科大讯飞 App ID / API Key / API Secret**: https://console.xfyun.cn/
- **阿里云 Access Key** (可选，普通话 ASR 备选): https://ram.console.aliyun.com/

### 3. 运行开发服务器

```bash
make dev
# 或
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

浏览器访问 http://localhost:8000 打开 Gradio UI，或访问 http://localhost:8000/docs 查看 API 文档。

### 4. 运行测试

```bash
make test
# 或
pytest tests/ -v
```

### 5. Docker 部署

```bash
make docker-build
make docker-up
```

## 架构概览

```
用户 → Gradio UI → FastAPI → 语音管道 → ASR → 方言引擎 → LLM → TTS → 用户
                              (讯飞)    (普转)  (通义)   (讯飞)
```

详见 `docs/architecture.md`。

## 新增方言

1. 在 `app/dialect/adapter.py` 的 `DialectCode` 枚举添加编码
2. 在 `app/dialect/data/<方言>/dictionary.json` 添加词典
3. 在 `app/dialect/dialects/` 创建 `<方言>.py`，实现 `DialectAdapter` 子类并用 `@DialectRegistry.register` 装饰
4. 确认 ASR/TTS 供应商支持，在 `get_asr_config()` / `get_tts_config()` 中配置参数

无需修改任何管道代码。详见 `docs/dialect_guide.md`。

## 开发状态

- [x] 项目骨架
- [x] 方言引擎 (粤语/四川话/普通话)
- [x] LLM 适配层 (通义千问)
- [x] 对话引擎 + 记忆管理
- [x] Gradio 适老化 UI
- [x] REST API + WebSocket 端点
- [ ] 讯飞 ASR/TTS 集成 (待填充)
- [ ] 阿里云 ASR 集成 (待填充)
- [ ] 端到端语音对话测试

## 许可证

MIT
