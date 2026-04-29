<template>
  <view class="ep-page">
    <view v-if="loading" class="empty">正在打开节目…</view>
    <view v-else-if="error" class="empty error">{{ error }}</view>
    <view v-else-if="ep">
      <view class="ep-tag">{{ categoryLabel }}</view>
      <text class="ep-title">{{ ep.title }}</text>
      <text class="ep-date">{{ ep.date }}</text>

      <view class="player">
        <view class="play-btn" @tap="togglePlay">
          <text class="play-icon">{{ playing ? '暂停' : '播放' }}</text>
        </view>
        <view class="progress-row">
          <text class="time">{{ fmt(currentMs) }}</text>
          <view class="track">
            <view class="bar" :style="{ width: progressPct + '%' }" />
          </view>
          <text class="time">{{ fmt(durationMs) }}</text>
        </view>
      </view>

      <scroll-view class="text-scroll" scroll-y :show-scrollbar="false">
        <text class="ep-text">{{ ep.text }}</text>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getRadioEpisode, radioAudioUrl, type RadioEpisode } from '../../api'

const ep = ref<RadioEpisode | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const playing = ref(false)
const currentMs = ref(0)
const durationMs = ref(0)
let audio: UniApp.InnerAudioContext | null = null

const categoryLabel = computed(() => {
  if (!ep.value) return ''
  if (ep.value.category === 'health') return '健康常识'
  if (ep.value.category === 'nostalgia')
    return ep.value.subtopic === 'opera' ? '戏曲赏析' : '怀旧时光'
  return ep.value.category
})

const progressPct = computed(() => {
  if (!durationMs.value) return 0
  return Math.min(100, Math.round((currentMs.value / durationMs.value) * 100))
})

onLoad((opt: any) => {
  const id = opt?.id
  if (!id) {
    error.value = '缺少节目编号'
    loading.value = false
    return
  }
  load(id)
})

async function load(id: string) {
  loading.value = true
  try {
    ep.value = await getRadioEpisode(id)
    if (ep.value.duration_ms) durationMs.value = ep.value.duration_ms
    if (ep.value.audio_url) prepareAudio(id)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function prepareAudio(id: string) {
  audio = uni.createInnerAudioContext()
  audio.src = radioAudioUrl(id)
  audio.onPlay(() => { playing.value = true })
  audio.onPause(() => { playing.value = false })
  audio.onStop(() => { playing.value = false; currentMs.value = 0 })
  audio.onEnded(() => { playing.value = false; currentMs.value = durationMs.value })
  audio.onTimeUpdate(() => {
    if (!audio) return
    currentMs.value = Math.round((audio.currentTime || 0) * 1000)
    if (!durationMs.value && audio.duration) {
      durationMs.value = Math.round(audio.duration * 1000)
    }
  })
  audio.onError((err) => {
    error.value = err.errMsg || '播放出错'
    playing.value = false
  })
}

function togglePlay() {
  if (!audio) return
  if (playing.value) audio.pause()
  else audio.play()
}

function fmt(ms: number): string {
  const total = Math.round(ms / 1000)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (audio) {
    try { audio.stop() } catch {}
    try { audio.destroy() } catch {}
    audio = null
  }
})
</script>

<style lang="scss" scoped>
.ep-page {
  padding: 48rpx 32rpx 96rpx;
  min-height: 100vh;
  background: #0E1116;
  color: #ECE7DD;
}

.empty {
  text-align: center;
  font-size: 28rpx;
  color: #8C857B;
  margin-top: 200rpx;
  font-family: 'Songti SC', serif;
  font-style: italic;
}
.error { color: #E89A92; }

.ep-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border: 1rpx solid #4FB58F;
  border-radius: 24rpx;
  font-size: 22rpx;
  color: #4FB58F;
  letter-spacing: 0.15em;
}
.ep-title {
  display: block;
  font-size: 60rpx;
  line-height: 1.4;
  font-weight: 300;
  letter-spacing: 0.06em;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
  margin-top: 24rpx;
}
.ep-date {
  display: block;
  font-size: 22rpx;
  color: #4A4540;
  letter-spacing: 0.2em;
  margin-top: 16rpx;
}

.player {
  margin-top: 64rpx;
  padding: 40rpx 32rpx;
  background: #161A20;
  border: 1rpx solid #1E232A;
  border-radius: 24rpx;
}
.play-btn {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  border: 1rpx solid #4FB58F;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}
.play-icon {
  font-size: 30rpx;
  color: #4FB58F;
  letter-spacing: 0.2em;
}
.progress-row {
  margin-top: 32rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.time {
  font-size: 22rpx;
  color: #8C857B;
  font-variant-numeric: tabular-nums;
}
.track {
  flex: 1;
  height: 4rpx;
  background: #1E232A;
  border-radius: 2rpx;
  overflow: hidden;
}
.bar {
  height: 100%;
  background: #4FB58F;
  transition: width 0.2s linear;
}

.text-scroll {
  margin-top: 48rpx;
  max-height: 700rpx;
}
.ep-text {
  font-size: 34rpx;
  line-height: 1.9;
  letter-spacing: 0.04em;
  color: #ECE7DD;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
  white-space: pre-wrap;
}
</style>
