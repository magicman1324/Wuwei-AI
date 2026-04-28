<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from './store/user'

onLaunch(() => {
  const userStore = useUserStore()
  userStore.init()
})
</script>

<style lang="scss">
/* ── 全局：暗色基底 ─────────────────────────────────────── */
page {
  font-size: 28rpx;
  line-height: 1.7;
  color: #ECE7DD;
  background: #0E1116;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 通用按钮 */
.btn-primary {
  background-color: #4FB58F;
  color: #0E1116;
  font-size: 30rpx;
  border-radius: 32rpx;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  letter-spacing: 0.1em;
}
.btn-primary:active { background-color: #3FA079; }

.text-primary { color: #4FB58F; }
.bg-primary { background-color: #4FB58F; }
</style>
