<template>
  <view class="history-page">
    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="error" class="error">{{ error }}</view>
    <view v-else-if="conversations.length === 0" class="empty">暂无对话记录</view>
    <view v-else class="list">
      <view
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-item"
        @tap="goDetail(conv.id)"
      >
        <view class="conv-header">
          <text class="conv-dialect">{{ dialectLabel(conv.dialect_used) }}</text>
          <text class="conv-count">{{ conv.message_count }}条消息</text>
        </view>
        <view class="conv-time">{{ formatTime(conv.started_at) }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { listConversations, type ConversationSummary } from '../../api'
import { useUserStore } from '../../store/user'
import { DIALECTS } from '../../utils/config'

const userStore = useUserStore()
const conversations = ref<ConversationSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  const userId = userStore.user?.id
  if (!userId) {
    error.value = '用户尚未初始化'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null
  try {
    conversations.value = await listConversations(userId)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})

function dialectLabel(code: string): string {
  return DIALECTS.find((d) => d.code === code)?.label || code
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时前`
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function goDetail(id: string) {
  // TODO: 对话详情页（分包）
  uni.showToast({ title: '详情页开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.history-page {
  padding: 32rpx 24rpx;
  min-height: 100vh;
  background: #0E1116;
  color: #ECE7DD;
}

.loading, .error, .empty {
  text-align: center;
  color: #8C857B;
  font-size: 30rpx;
  margin-top: 200rpx;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
  font-style: italic;
}

.error { color: #E89A92; }

.conv-item {
  background: #161A20;
  border: 1rpx solid #1E232A;
  border-radius: 16rpx;
  padding: 28rpx 32rpx;
  margin-bottom: 16rpx;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conv-dialect {
  font-size: 30rpx;
  font-weight: 400;
  color: #4FB58F;
  letter-spacing: 0.05em;
}

.conv-count {
  font-size: 24rpx;
  color: #8C857B;
}

.conv-time {
  font-size: 22rpx;
  color: #4A4540;
  margin-top: 8rpx;
  letter-spacing: 0.1em;
}
</style>
