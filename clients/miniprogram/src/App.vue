<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from './store/user'

onLaunch(() => {
  const userStore = useUserStore()
  userStore.init()
})
</script>

<style lang="scss">
/* 适老化全局样式 */
page {
  font-size: 36rpx;
  line-height: 1.8;
  color: #333333;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 全局按钮样式 */
.btn-primary {
  background-color: #2E7D32;
  color: #FFFFFF;
  font-size: 36rpx;
  border-radius: 32rpx;
  height: 96rpx;
  line-height: 96rpx;
  text-align: center;
}

.btn-primary:active {
  background-color: #1B5E20;
}

/* 无维绿色主题 */
.text-primary { color: #2E7D32; }
.bg-primary { background-color: #2E7D32; }
</style>
