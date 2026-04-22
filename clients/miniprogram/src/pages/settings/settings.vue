<template>
  <view class="settings-page">
    <!-- 用户信息 -->
    <view class="section">
      <view class="section-title">用户信息</view>
      <view class="card">
        <view class="row">
          <text class="label">用户ID</text>
          <text class="value">{{ userStore.user?.id?.substring(0, 8) || '-' }}</text>
        </view>
        <view class="row">
          <text class="label">昵称</text>
          <text class="value">{{ userStore.user?.display_name || '用户' }}</text>
        </view>
      </view>
    </view>

    <!-- 方言选择 -->
    <view class="section">
      <view class="section-title">方言偏好</view>
      <view class="card">
        <view
          v-for="d in DIALECTS"
          :key="d.code"
          class="radio-row"
          @tap="setDialect(d.code)"
        >
          <view
            class="radio-dot"
            :class="{ active: selectedDialect === d.code }"
          />
          <text class="radio-label">{{ d.label }}</text>
        </view>
      </view>
    </view>

    <!-- 语音设置 -->
    <view class="section">
      <view class="section-title">语音设置</view>
      <view class="card">
        <view class="slider-row">
          <text class="label">语速</text>
          <slider
            :value="ttsSpeed"
            :min="0.5"
            :max="1.5"
            :step="0.05"
            activeColor="#2E7D32"
            @change="(e: any) => ttsSpeed = e.detail.value"
          />
          <text class="slider-value">{{ ttsSpeed.toFixed(2) }}</text>
        </view>
        <view class="slider-row">
          <text class="label">音量</text>
          <slider
            :value="ttsVolume"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            activeColor="#2E7D32"
            @change="(e: any) => ttsVolume = e.detail.value"
          />
          <text class="slider-value">{{ ttsVolume.toFixed(1) }}</text>
        </view>
      </view>
    </view>

    <!-- 字号 -->
    <view class="section">
      <view class="section-title">字体大小</view>
      <view class="card font-row">
        <view
          v-for="fs in fontSizes"
          :key="fs.value"
          class="font-btn"
          :class="{ active: fontSize === fs.value }"
          @tap="fontSize = fs.value"
        >
          {{ fs.label }}
        </view>
      </view>
    </view>

    <!-- 保存 -->
    <view class="save-btn" :class="{ disabled: saving }" @tap="save">
      {{ saving ? '保存中...' : '保存设置' }}
    </view>

    <view v-if="message" class="message" :class="messageType">{{ message }}</view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { useChatStore } from '../../store/chat'
import { updatePreferences } from '../../api'
import { DIALECTS, type DialectCode } from '../../utils/config'

const userStore = useUserStore()
const chatStore = useChatStore()

const selectedDialect = ref<DialectCode>('cmn')
const ttsSpeed = ref(0.85)
const ttsVolume = ref(1.2)
const fontSize = ref('large')
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const fontSizes = [
  { value: 'large', label: '大' },
  { value: 'xlarge', label: '特大' },
  { value: 'xxlarge', label: '超大' },
]

onMounted(() => {
  if (userStore.user) {
    selectedDialect.value = (userStore.user.dialect_preference as DialectCode) || 'cmn'
    ttsSpeed.value = userStore.user.tts_speed
    ttsVolume.value = userStore.user.tts_volume
    fontSize.value = userStore.user.font_size
  }
})

function setDialect(code: DialectCode) {
  selectedDialect.value = code
  chatStore.dialect = code
}

async function save() {
  const userId = userStore.user?.id
  if (!userId || saving.value) return

  saving.value = true
  message.value = ''

  try {
    const updated = await updatePreferences(userId, {
      dialect_preference: selectedDialect.value,
      tts_speed: ttsSpeed.value,
      tts_volume: ttsVolume.value,
      font_size: fontSize.value,
    })
    userStore.user = updated

    uni.setStorageSync('dialect_preference', selectedDialect.value)
    message.value = '设置已保存'
    messageType.value = 'success'
  } catch (e: any) {
    message.value = e.message || '保存失败'
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.settings-page {
  padding: 24rpx;
  min-height: 100vh;
  background: #F5F5F5;
}

.section {
  margin-bottom: 32rpx;
}

.section-title {
  font-size: 30rpx;
  color: #666;
  margin-bottom: 12rpx;
  padding-left: 8rpx;
}

.card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx 32rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #F5F5F5;

  &:last-child { border-bottom: none; }
}

.label {
  font-size: 34rpx;
  color: #333;
}

.value {
  font-size: 32rpx;
  color: #999;
}

.radio-row {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #F5F5F5;

  &:last-child { border-bottom: none; }
}

.radio-dot {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 4rpx solid #BDBDBD;
  margin-right: 20rpx;

  &.active {
    border-color: #2E7D32;
    background: #2E7D32;
  }
}

.radio-label {
  font-size: 36rpx;
}

.slider-row {
  display: flex;
  align-items: center;
  padding: 16rpx 0;

  .label { width: 100rpx; }
  slider { flex: 1; margin: 0 16rpx; }
  .slider-value {
    width: 80rpx;
    text-align: right;
    font-size: 28rpx;
    color: #666;
  }
}

.font-row {
  display: flex;
  gap: 16rpx;
}

.font-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 12rpx;
  border: 2rpx solid #E0E0E0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  color: #666;

  &.active {
    border-color: #2E7D32;
    background: #E8F5E9;
    color: #2E7D32;
    font-weight: 600;
  }
}

.save-btn {
  margin-top: 40rpx;
  height: 96rpx;
  background: #2E7D32;
  color: #FFFFFF;
  font-size: 36rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.disabled { background: #BDBDBD; }
  &:active { background: #1B5E20; }
}

.message {
  text-align: center;
  font-size: 30rpx;
  margin-top: 20rpx;

  &.success { color: #2E7D32; }
  &.error { color: #D32F2F; }
}
</style>
