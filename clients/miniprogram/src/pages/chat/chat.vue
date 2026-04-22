<template>
  <view class="chat-page">
    <!-- 用户初始化中 -->
    <view v-if="userStore.loading" class="init-banner">
      正在初始化...
    </view>

    <!-- 用户初始化失败 -->
    <view v-else-if="userStore.error" class="error-banner" @tap="retryInit">
      {{ userStore.error }}（点击重试）
    </view>

    <!-- 聊天错误 -->
    <view v-else-if="chatStore.error" class="error-banner" @tap="chatStore.clearError">
      {{ chatStore.error }}（点击关闭）
    </view>

    <!-- 消息列表 -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-into-view="scrollTarget"
      scroll-with-animation
    >
      <view v-if="chatStore.messages.length === 0" class="empty-hint">
        按住下方麦克风开始聊天
      </view>
      <view
        v-for="(msg, i) in chatStore.messages"
        :key="i"
        :id="'msg-' + i"
        :class="['bubble-wrap', msg.role === 'user' ? 'bubble-right' : 'bubble-left']"
      >
        <view :class="['bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
          {{ msg.content }}
        </view>
      </view>
      <view id="scroll-bottom" style="height: 1rpx" />
    </scroll-view>

    <!-- 底部输入区 -->
    <view class="input-area">
      <!-- 麦克风模式 -->
      <view v-if="!showTextInput" class="mic-section">
        <view v-if="chatStore.isProcessing" class="processing-hint">正在处理...</view>
        <view
          class="mic-btn"
          :class="{ recording: chatStore.isRecording, disabled: chatStore.isProcessing || userStore.loading || !userStore.user }"
          @longpress="onMicStart"
          @touchend="onMicStop"
          @touchcancel="onMicCancel"
        >
          <text class="mic-icon">{{ chatStore.isRecording ? '⏹' : '🎤' }}</text>
        </view>
        <text class="mic-hint">{{ chatStore.isRecording ? '松开发送' : '按住说话' }}</text>
      </view>

      <!-- 文字输入模式 -->
      <view v-if="showTextInput" class="text-section">
        <input
          v-model="inputText"
          class="text-input"
          placeholder="输入消息..."
          :disabled="chatStore.isProcessing"
          confirm-type="send"
          @confirm="onSendText"
        />
        <view
          class="send-btn"
          :class="{ disabled: chatStore.isProcessing || !inputText.trim() || userStore.loading || !userStore.user }"
          @tap="onSendText"
        >
          发送
        </view>
      </view>

      <!-- 切换按钮 -->
      <view class="toggle-btn" @tap="showTextInput = !showTextInput">
        {{ showTextInput ? '🎤 切换语音' : '⌨️ 切换键盘' }}
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '../../store/chat'
import { useUserStore } from '../../store/user'

const chatStore = useChatStore()
const userStore = useUserStore()

const inputText = ref('')
const showTextInput = ref(false)
const scrollTarget = ref('')

function retryInit() {
  userStore.init()
}

// 如果进页面时用户还没初始化，等待初始化完成
onMounted(() => {
  if (!userStore.user && !userStore.loading) {
    userStore.init()
  }
})

// 录音管理器
const recorderManager = uni.getRecorderManager()
let tempFilePath = ''

recorderManager.onStop((res: any) => {
  tempFilePath = res.tempFilePath
  if (chatStore.isRecording) {
    // 正常结束 → 发送
    chatStore.isRecording = false
    sendVoice()
  }
})

recorderManager.onError(() => {
  chatStore.isRecording = false
  chatStore.error = '录音失败，请检查麦克风权限'
})

watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      scrollTarget.value = 'scroll-bottom'
    })
  },
)

function onMicStart() {
  if (chatStore.isProcessing) return

  uni.authorize({
    scope: 'scope.record',
    success: () => {
      chatStore.isRecording = true
      recorderManager.start({
        duration: 60000,
        sampleRate: 16000,
        numberOfChannels: 1,
        format: 'mp3',
      })
    },
    fail: () => {
      chatStore.error = '请在设置中允许录音权限'
    },
  })
}

function onMicStop() {
  if (!chatStore.isRecording) return
  recorderManager.stop()
}

function onMicCancel() {
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

  try {
    const res: any = await new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `http://127.0.0.1:8000/api/v1/voice`,
        filePath: tempFilePath,
        name: 'audio',
        formData: {
          user_id: userId,
          dialect_hint: chatStore.dialect,
          audio_format: 'mp3',
          sample_rate: '16000',
        },
        success: (r) => (r.statusCode < 300 ? resolve(JSON.parse(r.data as string)) : reject(new Error(`${r.statusCode}`))),
        fail: (e) => reject(new Error(e.errMsg)),
      })
    })

    chatStore.messages.push(
      { role: 'user', content: res.recognized_text },
      { role: 'assistant', content: res.response_text },
    )

    // 播放 TTS
    if (res.audio_base64) {
      playTtsAudio(res.audio_base64)
    }
  } catch (e: any) {
    chatStore.error = e.message || '语音识别失败'
  } finally {
    chatStore.isProcessing = false
    tempFilePath = ''
  }
}

function playTtsAudio(base64: string) {
  const fs = uni.getFileSystemManager()
  const filePath = `${wx.env.USER_DATA_PATH}/tts_reply.mp3`
  const buffer = uni.base64ToArrayBuffer(base64)
  fs.writeFileSync(filePath, buffer, 'binary')

  const audio = uni.createInnerAudioContext()
  chatStore.isPlaying = true
  audio.src = filePath
  audio.onEnded(() => {
    chatStore.isPlaying = false
    audio.destroy()
  })
  audio.onError(() => {
    chatStore.isPlaying = false
    audio.destroy()
  })
  audio.play()
}

async function onSendText() {
  const text = inputText.value.trim()
  if (!text) return

  const userId = userStore.user?.id
  if (!userId) {
    chatStore.error = '用户尚未初始化，请稍候'
    return
  }

  inputText.value = ''
  await chatStore.sendText(text, userId)
}
</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.init-banner {
  background: #E8F5E9;
  color: #2E7D32;
  font-size: 30rpx;
  padding: 16rpx 24rpx;
  text-align: center;
}

.error-banner {
  background: #FFF3E0;
  color: #E65100;
  font-size: 30rpx;
  padding: 16rpx 24rpx;
  text-align: center;
}

.message-list {
  flex: 1;
  padding: 20rpx 24rpx;
}

.empty-hint {
  text-align: center;
  color: #999;
  font-size: 36rpx;
  margin-top: 200rpx;
}

.bubble-wrap {
  display: flex;
  margin-bottom: 20rpx;
}

.bubble-right {
  justify-content: flex-end;
}

.bubble-left {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 20rpx 28rpx;
  border-radius: 24rpx;
  font-size: 36rpx;
  line-height: 1.6;
  word-break: break-all;
}

.bubble-user {
  background: #2E7D32;
  color: #FFFFFF;
  border-bottom-right-radius: 8rpx;
}

.bubble-ai {
  background: #FFFFFF;
  color: #333333;
  border-bottom-left-radius: 8rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
}

.input-area {
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #FFFFFF;
  border-top: 1rpx solid #EEEEEE;
}

.mic-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
}

.processing-hint {
  font-size: 30rpx;
  color: #666;
  margin-bottom: 16rpx;
}

.mic-btn {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: #2E7D32;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(46, 125, 50, 0.3);

  &.recording {
    background: #D32F2F;
    box-shadow: 0 8rpx 24rpx rgba(211, 47, 47, 0.3);
  }

  &.disabled {
    background: #BDBDBD;
    box-shadow: none;
  }
}

.mic-icon {
  font-size: 72rpx;
}

.mic-hint {
  margin-top: 12rpx;
  font-size: 28rpx;
  color: #999;
}

.text-section {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.text-input {
  flex: 1;
  height: 88rpx;
  border: 2rpx solid #E0E0E0;
  border-radius: 16rpx;
  padding: 0 24rpx;
  font-size: 36rpx;
}

.send-btn {
  width: 140rpx;
  height: 88rpx;
  background: #2E7D32;
  color: #FFFFFF;
  font-size: 32rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.disabled {
    background: #BDBDBD;
  }
}

.toggle-btn {
  text-align: center;
  font-size: 28rpx;
  color: #2E7D32;
  padding: 16rpx 0 0;
}
</style>
