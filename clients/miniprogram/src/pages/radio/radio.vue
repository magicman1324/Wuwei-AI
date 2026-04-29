<template>
  <view class="radio-page">
    <view class="header">
      <text class="title">电台</text>
      <text class="subtitle">每天两期，伴您一段时光</text>
    </view>

    <view v-if="loading" class="empty">正在调收音机…</view>
    <view v-else-if="error" class="empty error">{{ error }}</view>
    <view v-else-if="episodes.length === 0" class="empty">今日节目正在准备…</view>
    <view v-else class="list">
      <view
        v-for="ep in episodes"
        :key="ep.id"
        class="card"
        @tap="goPlay(ep.id)"
      >
        <view class="card-tag">{{ categoryLabel(ep.category, ep.subtopic) }}</view>
        <text class="card-title">{{ ep.title }}</text>
        <view class="card-meta">
          <text class="meta-date">{{ ep.date }}</text>
          <text v-if="ep.duration_ms" class="meta-dur">
            {{ formatDuration(ep.duration_ms) }}
          </text>
        </view>
      </view>
    </view>

    <view v-if="!loading && history.length > 0" class="history">
      <text class="history-title">往期回顾</text>
      <view
        v-for="ep in history"
        :key="ep.id"
        class="history-item"
        @tap="goPlay(ep.id)"
      >
        <text class="hi-tag">{{ categoryLabel(ep.category, ep.subtopic) }}</text>
        <text class="hi-title">{{ ep.title }}</text>
        <text class="hi-date">{{ ep.date }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getRadioToday, listRadioEpisodes, type RadioEpisode } from '../../api'

const today = ref<RadioEpisode[]>([])
const all = ref<RadioEpisode[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const episodes = today
const history = ref<RadioEpisode[]>([])

async function load() {
  loading.value = true
  error.value = null
  try {
    const [t, list] = await Promise.all([
      getRadioToday('cmn'),
      listRadioEpisodes(14, 'cmn'),
    ])
    today.value = t
    all.value = list
    const todayIds = new Set(t.map((e) => e.id))
    history.value = list.filter((e) => !todayIds.has(e.id))
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onShow(load)

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})

function categoryLabel(category: string, subtopic: string | null): string {
  if (category === 'health') return '健康常识'
  if (category === 'nostalgia') {
    if (subtopic === 'opera') return '戏曲赏析'
    return '怀旧时光'
  }
  return category
}

function formatDuration(ms: number): string {
  const total = Math.round(ms / 1000)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function goPlay(id: string) {
  uni.navigateTo({ url: `/pages/radio/episode?id=${id}` })
}
</script>

<style lang="scss" scoped>
.radio-page {
  padding: 48rpx 32rpx 64rpx;
  min-height: 100vh;
  background: #0E1116;
  color: #ECE7DD;
}

.header {
  margin-bottom: 48rpx;
}
.title {
  font-size: 64rpx;
  letter-spacing: 0.15em;
  font-weight: 300;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}
.subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #8C857B;
  font-style: italic;
  letter-spacing: 0.2em;
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

.list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.card {
  background: linear-gradient(180deg, #161A20 0%, #11151B 100%);
  border: 1rpx solid #1E232A;
  border-radius: 20rpx;
  padding: 36rpx 32rpx;
}
.card-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border: 1rpx solid #4FB58F;
  border-radius: 24rpx;
  font-size: 22rpx;
  color: #4FB58F;
  letter-spacing: 0.15em;
  margin-bottom: 20rpx;
}
.card-title {
  display: block;
  font-size: 44rpx;
  line-height: 1.4;
  letter-spacing: 0.05em;
  font-weight: 300;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}
.card-meta {
  margin-top: 24rpx;
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: #4A4540;
  letter-spacing: 0.1em;
}

.history {
  margin-top: 64rpx;
}
.history-title {
  display: block;
  font-size: 24rpx;
  color: #4A4540;
  letter-spacing: 0.3em;
  margin-bottom: 24rpx;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #1E232A;
}
.hi-tag {
  font-size: 20rpx;
  color: #4FB58F;
  letter-spacing: 0.15em;
  flex-shrink: 0;
}
.hi-title {
  flex: 1;
  font-size: 28rpx;
  color: #ECE7DD;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hi-date {
  font-size: 20rpx;
  color: #4A4540;
  flex-shrink: 0;
}
</style>
