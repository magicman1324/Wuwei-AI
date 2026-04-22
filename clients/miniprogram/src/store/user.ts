import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createUser, getUser, type UserResponse } from '../api'

function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

export const useUserStore = defineStore('user', () => {
  const user = ref<UserResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function getUserId(): string | null {
    return uni.getStorageSync('user_id') || null
  }

  function getDeviceId(): string {
    let id = uni.getStorageSync('device_id') as string
    if (!id) {
      id = uuid()
      uni.setStorageSync('device_id', id)
    }
    return id
  }

  async function init() {
    loading.value = true
    error.value = null

    try {
      const userId = getUserId()
      if (userId) {
        try {
          user.value = await getUser(userId)
          return
        } catch {
          uni.removeStorageSync('user_id')
        }
      }

      const deviceId = getDeviceId()
      const dialect = (uni.getStorageSync('dialect_preference') as string) || 'cmn'
      user.value = await createUser({
        device_id: deviceId,
        dialect_preference: dialect,
      })
      uni.setStorageSync('user_id', user.value.id)
    } catch (e: any) {
      error.value = e.message || '用户初始化失败'
    } finally {
      loading.value = false
    }
  }

  return { user, loading, error, init, getUserId, getDeviceId }
})
