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
  padding: 24rpx;
  min-height: 100vh;
  background: #F5F5F5;
}

.loading, .error, .empty {
  text-align: center;
  color: #999;
  font-size: 36rpx;
  margin-top: 200rpx;
}

.error { color: #E65100; }

.conv-item {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 28rpx 32rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conv-dialect {
  font-size: 34rpx;
  font-weight: 600;
  color: #2E7D32;
}

.conv-count {
  font-size: 28rpx;
  color: #999;
}

.conv-time {
  font-size: 26rpx;
  color: #BDBDBD;
  margin-top: 8rpx;
}
</style>
