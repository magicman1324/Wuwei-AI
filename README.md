# 无维AI (Wuwei-AI)

面向中老年用户的方言语音聊天 AI 与日更电台。"无维"取自无维科技，寓意让老人与 AI 的对话如同与家人闲聊一般自然——不需要学习新技能，不需要适应普通话。

## 核心特性

- **语音优先交互**：按住说话，自动回复
- **方言支持**：MVP 支持普通话、粤语、四川话，架构可扩展更多方言
- **老年电台**：每天 06:00 自动生成「健康」「怀旧+戏曲」两期 3-4 分钟节目，主播音色播报
- **适老化设计**：大字体、大按钮、高对比度 UI，语速可调
- **国产大模型**：基于通义千问 (Qwen) LLM
- **温暖人格**：耐心、体贴、口语化，像贴心晚辈

## 技术栈

- **后端**：Python 3.11 + FastAPI + Uvicorn + SQLModel + APScheduler
- **客户端**：微信小程序 (Uniapp + Vue 3)、Flutter（双端共享后端）
- **数据库**：SQLite
- **LLM**：通义千问 (Qwen) — 阿里云 DashScope
- **ASR**：科大讯飞（方言）
- **TTS**：科大讯飞（聊天）+ 火山引擎 BigTTS（电台主播音色）
- **部署**：Docker + Docker Compose

## 项目结构

```
Wuwei-AI/
├── app/
│   ├── main.py              # FastAPI 入口（含电台 scheduler 生命周期）
│   ├── config.py            # pydantic-settings 配置
│   ├── api/v1/              # REST 路由（chat / voice / radio …）
│   ├── speech/              # ASR / TTS / Pipeline（讯飞 + 火山）
│   ├── dialect/             # 方言适配器注册表
│   ├── chat/                # 对话引擎（LLM / Memory / Prompt）
│   ├── radio/               # 老年电台（生成器 / 调度 / 选题）
│   └── db/                  # SQLModel ORM
├── clients/
│   ├── miniprogram/         # 微信小程序（Uniapp Vue3）
│   └── flutter_app/         # Flutter 客户端
├── tests/
├── pyproject.toml
└── docker-compose.yml
```

## 快速开始

### 1. 安装依赖

```bash
pip install uv
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入：

```
# 通义千问
WUWEI_LLM_API_KEY=sk-...

# 科大讯飞（聊天 ASR/TTS）
WUWEI_IFLYTEK_APP_ID=...
WUWEI_IFLYTEK_API_KEY=...
WUWEI_IFLYTEK_API_SECRET=...

# 火山引擎 BigTTS（电台主播音色，可选）
WUWEI_VOLCANO_APP_ID=...
WUWEI_VOLCANO_ACCESS_TOKEN=...
WUWEI_RADIO_TTS_PROVIDER=volcano
WUWEI_RADIO_TTS_VOICE=zh_male_beijingxiaoye_moon_bigtts
```

密钥申请：
- 通义千问：https://dashscope.console.aliyun.com/
- 科大讯飞：https://console.xfyun.cn/
- 火山引擎语音合成大模型：https://console.volcengine.com/speech/

### 3. 运行后端

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档：http://localhost:8000/docs
- 电台手动生成：`POST /api/v1/radio/admin/generate` body `{"force": true}`
- 当日节目：`GET /api/v1/radio/today?dialect=cmn`

### 4. 运行客户端

**微信小程序**：
```bash
cd clients/miniprogram
npm install
npm run dev:mp-weixin
```
用微信开发者工具导入 `dist/dev/mp-weixin/`。

**Flutter**：
```bash
cd clients/flutter_app
flutter pub get
flutter run
```

### 5. Docker 部署

```bash
docker compose up -d
```

## 架构概览

```
聊天链路：用户 → 客户端 → FastAPI → ASR(讯飞) → 方言规范化 → LLM(通义) → TTS(讯飞) → 用户
电台链路：APScheduler 06:00 → 选题 → LLM 写稿 800-1200 字 → BigTTS 分段合成 → MP3 → DB
```

## 新增方言

1. 在 `app/dialect/adapter.py` 的 `DialectCode` 枚举添加编码
2. 在 `app/dialect/data/<方言>/dictionary.json` 添加词典
3. 在 `app/dialect/dialects/` 创建 `<方言>.py`，实现 `DialectAdapter` 子类并用 `@DialectRegistry.register` 装饰
4. 确认 ASR/TTS 供应商支持，在 `get_asr_config()` / `get_tts_config()` 中配置参数

无需修改管道代码。

## 开发状态

- [x] 方言引擎（粤语/四川话/普通话）
- [x] LLM 适配层（通义千问）+ 记忆管理
- [x] 讯飞 ASR/TTS 集成
- [x] 微信小程序客户端 + Flutter 客户端
- [x] 老年电台（健康 + 怀旧+戏曲，火山 BigTTS）
- [ ] 子女端（健康关怀仪表盘）
- [ ] 防诈盾
- [ ] 老友圈

## 许可证

MIT
