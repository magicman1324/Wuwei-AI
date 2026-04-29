<template>
  <view class="chat-page" :class="`state-${uiState}`">
    <!-- 顶部错误条（聊天 API 错误） -->
    <view v-if="chatStore.error" class="banner banner-warn" @tap="chatStore.clearError">
      {{ chatStore.error }}（点击关闭）
    </view>

    <!-- 主响应区 -->
    <view class="response-area">
      <!-- 用户初始化中：占满主区，居中提示 -->
      <view v-if="userStore.loading" class="boot-block fade-up">
        <view class="boot-spinner" />
        <text class="boot-title">正在连接服务…</text>
        <text class="boot-url">{{ apiBase }}</text>
      </view>

      <!-- 用户初始化失败：占满主区 -->
      <view v-else-if="!userStore.user" class="boot-block fade-up">
        <text class="boot-title boot-title-error">未连接服务</text>
        <text class="boot-msg">{{ userStore.error || '后端尚未响应，请检查' }}</text>
        <text class="boot-url">{{ apiBase }}</text>
        <view class="boot-actions">
          <view class="boot-btn" @tap="retryInit">重试</view>
          <view class="boot-btn" @tap="pingHealth">测试连接</view>
        </view>
        <text class="boot-hint">
          若 cpolar 隧道地址变了，请改 src/utils/config.ts 中的 HOSTS.tunnel
        </text>
      </view>

      <!-- idle: 品牌+提示 -->
      <view v-else-if="uiState === 'idle'" class="idle-block fade-up">
        <text class="brand">无维</text>
        <text class="brand-sub">按住说话，或输入问题</text>
      </view>

      <!-- listening: 实时识别文本（mp 没有 Web Speech，用占位语） -->
      <view v-else-if="userStore.user && uiState === 'listening'" class="listen-block fade-up">
        <text class="listen-hint">正在聆听…</text>
      </view>

      <!-- thinking: 三个跳动的点 + 思考中 -->
      <view v-else-if="userStore.user && uiState === 'thinking'" class="think-block fade-up">
        <view class="dots">
          <view class="dot" />
          <view class="dot" />
          <view class="dot" />
        </view>
        <text class="think-label">{{ thinkPhrase }}</text>
      </view>

      <!-- responding: 大字号 AI 回复（带打字机） -->
      <scroll-view
        v-else-if="userStore.user && uiState === 'responding'"
        class="resp-scroll fade-up"
        scroll-y
        :scroll-into-view="respAnchor"
        :scroll-with-animation="true"
        :enhanced="true"
        :show-scrollbar="false"
      >
        <view class="resp-block">
          <text class="resp-text" :class="respFontClass">{{ typedText }}</text>
          <text v-if="!typingDone" class="caret">▏</text>
          <view class="resp-actions" v-if="typingDone">
            <view class="done-btn" @tap="dismissResponse">完成</view>
          </view>
          <view id="resp-end" class="resp-end-anchor" />
        </view>
      </scroll-view>
    </view>

    <!-- 录音按钮 -->
    <view class="mic-row">
      <view class="mic-stack">
        <view v-if="chatStore.isRecording" class="ring ring-1" />
        <view v-if="chatStore.isRecording" class="ring ring-2" />
        <view v-if="chatStore.isProcessing" class="thinking-arc" />
        <view
          class="mic-btn"
          :class="{
            recording: chatStore.isRecording,
            thinking: chatStore.isProcessing,
            idle: !chatStore.isRecording && !chatStore.isProcessing,
            disabled: userStore.loading || !userStore.user,
          }"
          @touchstart="onMicTouchStart"
          @touchend="onMicTouchEnd"
          @touchcancel="onMicTouchCancel"
        >
          <!-- listening: wave bars -->
          <view v-if="chatStore.isRecording" class="wave">
            <view v-for="i in 7" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.1}s` }" />
          </view>
          <!-- thinking: clock -->
          <text v-else-if="chatStore.isProcessing" class="mic-glyph">⏱</text>
          <!-- idle: mic glyph -->
          <text v-else class="mic-glyph">🎙</text>
        </view>
      </view>
      <text class="mic-cap">
        {{ chatStore.isRecording ? '松开发送' : chatStore.isProcessing ? '思考中' : '按住说话' }}
      </text>
    </view>

    <!-- 底栏：电台入口 + 历史 chips + 输入框 -->
    <view class="bottom-bar">
      <scroll-view
        class="chip-row"
        scroll-x
        :show-scrollbar="false"
      >
        <view class="chip chip-radio" @tap="goRadio">电台 · 今日两期</view>
        <view
          v-for="(item, i) in historyChips"
          :key="i"
          class="chip"
          @tap="recallHistory(item)"
        >
          {{ item.q }}
        </view>
      </scroll-view>

      <view class="input-row">
        <input
          v-model="inputText"
          class="text-input"
          placeholder="或者直接输入…"
          placeholder-class="input-placeholder"
          :disabled="chatStore.isRecording"
          confirm-type="send"
          confirm-hold
          :cursor-spacing="20"
          :adjust-position="true"
          @confirm="onSendText"
        />
        <button
          class="send-btn"
          :class="{ active: canSend }"
          :disabled="!canSend"
          hover-class="send-btn-hover"
          :hover-stay-time="80"
          @tap="onSendText"
        >
          发送
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useChatStore, type ChatMessage } from '../../store/chat'
import { useUserStore } from '../../store/user'
import { BASE_URL } from '../../utils/config'
import { healthCheck } from '../../api'

const chatStore = useChatStore()
const userStore = useUserStore()

const inputText = ref('')
const dismissed = ref(false)
const apiBase = computed(() => BASE_URL)

// 发送按钮是否可用：有文字 + 用户已就绪 + 不在录音/处理中
const canSend = computed(() =>
  !!inputText.value.trim() &&
  !!userStore.user &&
  !chatStore.isProcessing &&
  !chatStore.isRecording
)

// 等待期方言安抚语：按方言随机抽词、4 秒换一句
const THINK_PHRASES: Record<string, string[]> = {
  cmn: [
    '正在努力想呢…',
    '稍等我想想…',
    '让我捋一捋…',
    '马上就好…',
  ],
  yue: [
    '等等啊，我谂紧…',
    '畀啲时间我啦…',
    '做紧嘢，唔使急…',
    '即刻就嚟…',
  ],
  'cmn-sichuan': [
    '莫慌嘛，我想哈儿…',
    '等哈嘛，马上就来…',
    '让我捋哈儿…',
    '一哈儿就好…',
  ],
}
function pickPhrase(dialect: string): string {
  const pool = THINK_PHRASES[dialect] || THINK_PHRASES.cmn
  return pool[Math.floor(Math.random() * pool.length)]
}
const thinkPhrase = ref('正在努力想呢…')
let thinkTimer: any = null

// 派生 UI 状态机
const uiState = computed<'idle' | 'listening' | 'thinking' | 'responding'>(() => {
  if (chatStore.isRecording) return 'listening'
  if (chatStore.isProcessing) return 'thinking'
  if (latestAssistant.value && !dismissed.value) return 'responding'
  return 'idle'
})

const latestAssistant = computed(() => {
  for (let i = chatStore.messages.length - 1; i >= 0; i--) {
    if (chatStore.messages[i].role === 'assistant') return chatStore.messages[i].content
  }
  return ''
})

const latestUser = computed(() => {
  for (let i = chatStore.messages.length - 1; i >= 0; i--) {
    if (chatStore.messages[i].role === 'user') return chatStore.messages[i].content
  }
  return ''
})

// 历史 chips：取所有 user 消息，去重保序，最多 5 条，新的在前
const historyChips = computed(() => {
  const seen = new Set<string>()
  const out: { q: string; idx: number }[] = []
  for (let i = chatStore.messages.length - 1; i >= 0; i--) {
    const m = chatStore.messages[i]
    if (m.role === 'user' && !seen.has(m.content)) {
      seen.add(m.content)
      out.push({ q: m.content, idx: i })
      if (out.length >= 5) break
    }
  }
  // 跳过最近一次（已在大字回复区显示）
  return out.slice(1)
})

// ── 打字机 ───────────────────────────────────────────────────────────────
const typedText = ref('')
const typingDone = ref(false)
const respAnchor = ref('')
let typeTimer: any = null

// 字号自适应：长文略缩
const respFontClass = computed(() => {
  const len = (typedText.value || latestAssistant.value || '').length
  return len > 60 ? 'resp-text-sm' : 'resp-text-lg'
})

// 监听思考态：进入时立刻挑一句，每 4 秒换一句；离开时清掉计时器
watch(uiState, (s) => {
  if (s === 'thinking') {
    const dialect = userStore.user?.dialect_preference || 'cmn'
    thinkPhrase.value = pickPhrase(dialect)
    if (thinkTimer) clearInterval(thinkTimer)
    thinkTimer = setInterval(() => {
      thinkPhrase.value = pickPhrase(dialect)
    }, 4000)
  } else if (thinkTimer) {
    clearInterval(thinkTimer)
    thinkTimer = null
  }
})

// 兜底打字机：只在没有 TTS 音频时（讯飞失败）按时间推进
watch(latestAssistant, (text) => {
  if (typeTimer) clearInterval(typeTimer)
  typedText.value = ''
  typingDone.value = false
  if (!text) return
  // 若 1 秒内没有音频接管，启用兜底打字机
  setTimeout(() => {
    if (audioDriving) return // 音频已接管
    let i = 0
    typeTimer = setInterval(() => {
      i++
      typedText.value = text.slice(0, i)
      respAnchor.value = ''
      setTimeout(() => { respAnchor.value = 'resp-end' }, 0)
      if (i >= text.length) {
        clearInterval(typeTimer)
        typingDone.value = true
      }
    }, 28)
  }, 1000)
})

function dismissResponse() {
  dismissed.value = true
}

function recallHistory(item: { q: string; idx: number }) {
  // 找到对应的 assistant 回复并展示
  const assistant = chatStore.messages[item.idx + 1]
  if (assistant && assistant.role === 'assistant') {
    typedText.value = assistant.content
    typingDone.value = true
    dismissed.value = false
  }
}

function goRadio() {
  uni.navigateTo({ url: '/pages/radio/radio' })
}

// ── 用户初始化 ───────────────────────────────────────────────────────────
function retryInit() {
  userStore.init()
}

async function pingHealth() {
  uni.showLoading({ title: '测试中…', mask: true })
  try {
    const res = await healthCheck()
    uni.hideLoading()
    uni.showModal({
      title: '连接成功',
      content: `service: ${res.service}\nstatus: ${res.status}`,
      showCancel: false,
    })
  } catch (e: any) {
    uni.hideLoading()
    uni.showModal({
      title: '连接失败',
      content: `${e?.message || e}\n\n${BASE_URL}`,
      showCancel: false,
    })
  }
}

onMounted(() => {
  if (!userStore.user && !userStore.loading) {
    userStore.init()
  }
})

// ── 录音 ────────────────────────────────────────────────────────────────
const recorderManager = uni.getRecorderManager()
let tempFilePath = ''
let recordStartedAt = 0
const MIN_RECORD_MS = 500 // 短于 500ms 视为误触，丢弃

recorderManager.onStart(() => {
  console.log('[mic] onStart')
})

recorderManager.onStop((res: any) => {
  const dur = Date.now() - recordStartedAt
  tempFilePath = res.tempFilePath
  console.log('[mic] onStop', { duration: dur, tempFilePath, fileSize: res.fileSize })
  if (chatStore.isRecording) {
    chatStore.isRecording = false
    if (dur < MIN_RECORD_MS) {
      uni.showToast({ title: '录音太短，请按住说话', icon: 'none', duration: 1200 })
      tempFilePath = ''
      return
    }
    // 触觉反馈：录音结束、开始处理
    uni.vibrateShort?.({ type: 'medium' as any })
    sendVoice()
  }
})

recorderManager.onError((err: any) => {
  console.error('[mic] onError', err)
  chatStore.isRecording = false
  uni.showModal({
    title: '需要麦克风权限',
    content: '请点击"前往设置"，在小程序权限中开启麦克风',
    confirmText: '前往设置',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) uni.openSetting({ success: () => {} })
    },
  })
})

function onMicTouchStart() {
  if (chatStore.isProcessing) return
  if (!userStore.user) {
    uni.showToast({ title: '正在初始化用户…', icon: 'none' })
    return
  }
  dismissed.value = true // 一开始录音就隐藏上一条回复
  recordStartedAt = Date.now()
  chatStore.isRecording = true
  console.log('[mic] start recording')
  // 触觉反馈：录音开始
  uni.vibrateShort?.({ type: 'light' as any })
  recorderManager.start({
    duration: 60000,
    sampleRate: 16000,
    numberOfChannels: 1,
    format: 'mp3',
  })
}

function onMicTouchEnd() {
  if (!chatStore.isRecording) return
  console.log('[mic] touchend → stop')
  recorderManager.stop()
}

function onMicTouchCancel() {
  if (!chatStore.isRecording) return
  console.log('[mic] touchcancel → cancel')
  chatStore.isRecording = false
  recorderManager.stop()
  tempFilePath = ''
}

async function sendVoice() {
  if (!tempFilePath) return
  const userId = userStore.user?.id
  if (!userId) {
    chatStore.error = '用户尚未初始化，请稍候'
    return
  }

  chatStore.isProcessing = true
  chatStore.error = null
  console.log('[voice] uploading', { url: `${BASE_URL}/voice`, userId, dialect: chatStore.dialect })

  try {
    const res: any = await new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${BASE_URL}/voice`,
        filePath: tempFilePath,
        name: 'audio',
        formData: {
          user_id: userId,
          dialect_hint: chatStore.dialect,
          audio_format: 'mp3',
          sample_rate: '16000',
        },
        success: (r) => {
          console.log('[voice] uploadFile success', { status: r.statusCode, dataLen: (r.data as string)?.length })
          if (r.statusCode < 300) {
            try {
              resolve(JSON.parse(r.data as string))
            } catch (e) {
              reject(new Error('响应解析失败'))
            }
          } else {
            reject(new Error(`服务器 ${r.statusCode}: ${(r.data as string).slice(0, 200)}`))
          }
        },
        fail: (e) => {
          console.error('[voice] uploadFile fail', e)
          reject(new Error(e.errMsg))
        },
      })
    })

    console.log('[voice] response', res)
    const recognized: string = (res.recognized_text || '').trim()
    const reply: string = (res.response_text || '').trim()

    if (!recognized && !reply) {
      uni.showToast({ title: '没听清，请再说一遍', icon: 'none', duration: 1500 })
      return
    }

    chatStore.messages.push(
      { role: 'user', content: recognized || '(未识别)' } as ChatMessage,
      { role: 'assistant', content: reply || '我没听清楚，能再说一遍吗？' } as ChatMessage,
    )
    dismissed.value = false
    // 触觉反馈：收到回复
    uni.vibrateShort?.({ type: 'light' as any })

    if (res.audio_base64) playTtsAudio(res.audio_base64, reply || '我没听清楚，能再说一遍吗？')
  } catch (e: any) {
    console.error('[voice] error', e)
    chatStore.error = e.message || '语音识别失败'
  } finally {
    chatStore.isProcessing = false
    tempFilePath = ''
  }
}

let audioDriving = false

function playTtsAudio(base64: string, fullText: string) {
  const fs = uni.getFileSystemManager()
  const filePath = `${wx.env.USER_DATA_PATH}/tts_${Date.now()}_${Math.floor(Math.random() * 1e6)}.mp3`
  const buffer = uni.base64ToArrayBuffer(base64)
  fs.writeFileSync(filePath, buffer, 'binary')

  // 关掉时间打字机，由音频接管文字进度
  if (typeTimer) { clearInterval(typeTimer); typeTimer = null }
  audioDriving = true
  typedText.value = ''
  typingDone.value = false

  const audio = uni.createInnerAudioContext()
  chatStore.isPlaying = true
  audio.src = filePath

  audio.onTimeUpdate(() => {
    const dur = audio.duration || 0
    if (!dur || !fullText) return
    const ratio = Math.min(audio.currentTime / dur, 1)
    const cnt = Math.max(1, Math.floor(fullText.length * ratio))
    typedText.value = fullText.slice(0, cnt)
    respAnchor.value = ''
    setTimeout(() => { respAnchor.value = 'resp-end' }, 0)
  })

  const cleanup = () => {
    chatStore.isPlaying = false
    audioDriving = false
    typedText.value = fullText
    typingDone.value = true
    audio.destroy()
    try { fs.unlinkSync(filePath) } catch (_) { /* ignore */ }
  }
  audio.onEnded(cleanup)
  audio.onError(cleanup)
  audio.play()
}

async function onSendText() {
  console.log('[send] onSendText fired', { text: inputText.value, canSend: canSend.value })
  if (!canSend.value) return
  const text = inputText.value.trim()
  const userId = userStore.user!.id
  inputText.value = ''
  dismissed.value = false
  const ok = await chatStore.sendText(text, userId)
  if (ok) {
    // 触觉反馈：收到回复
    uni.vibrateShort?.({ type: 'light' as any })
  } else {
    // 失败：把文字还回输入框，方便重试
    inputText.value = text
  }
}
</script>

<style lang="scss" scoped>
/* ── 调色板（OKLCH 近似为 hex） ─────────────────────────── */
$bg: #0E1116;
$bg2: #161A20;
$bg3: #1E232A;
$fg: #ECE7DD;
$fg-dim: #8C857B;
$fg-dimmer: #4A4540;
$accent: #4FB58F;
$accent-glow: rgba(79, 181, 143, 0.25);
$serif: 'Songti SC', 'STSong', 'Noto Serif SC', 'STKaiti', serif;
$sans: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg;
  color: $fg;
  font-family: $sans;
  overflow: hidden;
}

/* ── Banner ─────────────────────────────────────────────── */
.banner {
  font-size: 24rpx;
  padding: 12rpx 24rpx;
  text-align: center;
  letter-spacing: 0.05em;
}
.banner-info { background: $bg2; color: $fg-dim; }
.banner-warn { background: rgba(217, 102, 91, 0.15); color: #E89A92; }

/* ── 主响应区 ─────────────────────────────────────────── */
.response-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 60rpx 40rpx;
  min-height: 0;
  overflow: hidden;
}

.idle-block {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.brand {
  font-size: 26rpx;
  color: $fg-dim;
  letter-spacing: 0.4em;
  text-transform: uppercase;
  margin-bottom: 24rpx;
  display: block;
}
.brand-sub {
  font-size: 32rpx;
  color: $fg-dimmer;
  font-family: $serif;
  font-style: italic;
  font-weight: 300;
  display: block;
}

.listen-block {
  text-align: center;
}
.listen-hint {
  font-size: 30rpx;
  color: $fg-dim;
  letter-spacing: 0.2em;
}

.think-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28rpx;
}
.think-label {
  font-size: 26rpx;
  color: $fg-dim;
  letter-spacing: 0.3em;
}
.dots {
  display: flex;
  gap: 16rpx;
}
.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: $fg-dim;
  animation: thinking-dot 1.4s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

.resp-scroll {
  width: 100%;
  max-height: 100%;
  /* mp-weixin scroll-view 默认 box; 居中靠内层 .resp-block */
}
.resp-block {
  text-align: center;
  max-width: 100%;
  padding: 20rpx 0;
}
.resp-end-anchor {
  height: 1rpx;
  width: 1rpx;
}
.resp-text {
  line-height: 1.4;
  font-weight: 300;
  font-family: $serif;
  letter-spacing: -0.01em;
  color: $fg;
  display: inline;
}
.resp-text-lg { font-size: 88rpx; }
.resp-text-sm { font-size: 60rpx; line-height: 1.5; }
.caret {
  display: inline-block;
  color: $accent;
  font-size: 80rpx;
  margin-left: 4rpx;
  animation: blink 0.8s step-end infinite;
}
.resp-actions {
  margin-top: 48rpx;
}
.done-btn {
  display: inline-block;
  padding: 12rpx 40rpx;
  border: 1rpx solid $bg3;
  border-radius: 40rpx;
  font-size: 24rpx;
  color: $fg-dim;
  letter-spacing: 0.2em;
}

/* ── 麦克风 ─────────────────────────────────────────────── */
.mic-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28rpx;
  padding: 16rpx 0 40rpx;
}
.mic-stack {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring {
  position: absolute;
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  border: 3rpx solid $accent;
  pointer-events: none;
}
.ring-1 { animation: pulse-ring 1.4s ease-out infinite; }
.ring-2 { animation: pulse-ring2 1.4s ease-out infinite 0.4s; }

.thinking-arc {
  position: absolute;
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  border: 3rpx solid transparent;
  border-top-color: $accent;
  border-right-color: $accent;
  animation: spin-slow 1.2s linear infinite;
}

.mic-btn {
  position: relative;
  z-index: 2;
  width: 168rpx;
  height: 168rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg2;
  border: 2rpx solid $bg3;
  transition: background 0.3s, border-color 0.3s;
}
.mic-btn.idle { animation: breathe 4s ease-in-out infinite; }
.mic-btn.recording {
  background: $accent;
  border-color: $accent;
  box-shadow: 0 0 0 0 $accent-glow, 0 8rpx 32rpx rgba(0,0,0,0.5);
}
.mic-btn.thinking { border-color: $accent; }
.mic-btn.disabled { opacity: 0.4; }

.mic-glyph {
  font-size: 56rpx;
  filter: grayscale(0.3);
}
.wave {
  display: flex;
  align-items: center;
  gap: 6rpx;
  height: 60rpx;
}
.wave-bar {
  width: 5rpx;
  border-radius: 4rpx;
  background: $bg;
  height: 12rpx;
  animation: wave 0.9s ease-in-out infinite;
}

.mic-cap {
  font-size: 22rpx;
  color: $fg-dimmer;
  letter-spacing: 0.3em;
  text-transform: uppercase;
}

/* ── 底栏 ──────────────────────────────────────────────── */
.bottom-bar {
  border-top: 1rpx solid $bg2;
  padding: 24rpx 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.chip-row {
  white-space: nowrap;
}
.chip {
  display: inline-block;
  padding: 8rpx 24rpx;
  margin-right: 12rpx;
  border: 1rpx solid $bg3;
  border-radius: 40rpx;
  font-size: 22rpx;
  color: $fg-dim;
  background: transparent;
  max-width: 360rpx;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chip-radio {
  border-color: $accent;
  color: $accent;
  letter-spacing: 0.1em;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.text-input {
  flex: 1;
  height: 76rpx;
  background: #11151B;
  border: 1rpx solid $bg3;
  border-radius: 20rpx;
  padding: 0 28rpx;
  font-size: 26rpx;
  color: $fg;
}
.input-placeholder {
  color: $fg-dimmer;
  font-family: $serif;
  font-style: italic;
}
/* mp-weixin 原生 button 默认样式很重，全部重置 */
.send-btn {
  padding: 0 28rpx;
  margin: 0;
  height: 76rpx;
  line-height: 76rpx;
  background: transparent;
  border: 1rpx solid $bg3;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: $fg-dim;
  text-align: center;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
  /* 去掉原生 button 边框 */
  &::after { border: none; }
}
.send-btn.active {
  color: $accent;
  border-color: $accent;
}
.send-btn[disabled] {
  background: transparent;
  color: $fg-dimmer;
  border-color: $bg3;
}
.send-btn-hover {
  background: rgba(79, 181, 143, 0.08) !important;
}

/* ── 启动/连接失败块 ──────────────────────────────────── */
.boot-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 24rpx;
  max-width: 600rpx;
}
.boot-spinner {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  border: 3rpx solid $bg3;
  border-top-color: $accent;
  animation: spin-slow 1s linear infinite;
  margin-bottom: 8rpx;
}
.boot-title {
  font-size: 32rpx;
  color: $fg-dim;
  letter-spacing: 0.2em;
}
.boot-title-error {
  color: #E89A92;
}
.boot-msg {
  font-size: 26rpx;
  color: $fg-dimmer;
  font-family: $serif;
  font-style: italic;
  line-height: 1.6;
}
.boot-url {
  font-size: 22rpx;
  color: $fg-dimmer;
  word-break: break-all;
  padding: 12rpx 20rpx;
  background: $bg2;
  border-radius: 8rpx;
  font-family: 'Menlo', 'Consolas', monospace;
}
.boot-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 12rpx;
}
.boot-btn {
  padding: 16rpx 40rpx;
  border: 1rpx solid $bg3;
  border-radius: 40rpx;
  font-size: 26rpx;
  color: $accent;
  background: $bg2;
  letter-spacing: 0.15em;
}
.boot-hint {
  font-size: 22rpx;
  color: $fg-dimmer;
  line-height: 1.6;
  margin-top: 8rpx;
  opacity: 0.7;
}

/* ── 动画 ──────────────────────────────────────────────── */
@keyframes pulse-ring {
  0%   { transform: scale(1);   opacity: 0.6; }
  100% { transform: scale(1.7); opacity: 0; }
}
@keyframes pulse-ring2 {
  0%   { transform: scale(1);   opacity: 0.4; }
  100% { transform: scale(2.1); opacity: 0; }
}
@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.04); }
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes fade-up {
  from { opacity: 0; transform: translateY(16rpx); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}
@keyframes wave {
  0%, 100% { height: 12rpx; }
  50%      { height: 56rpx; }
}
@keyframes thinking-dot {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40%           { opacity: 1;   transform: scale(1.2); }
}
.fade-up { animation: fade-up 0.5s ease both; }
</style>
