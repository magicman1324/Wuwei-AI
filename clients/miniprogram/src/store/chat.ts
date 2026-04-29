import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chat as apiChat, type ChatResponse } from '../api'
import type { DialectCode } from '../utils/config'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isProcessing = ref(false)
  const isRecording = ref(false)
  const isPlaying = ref(false)
  const dialect = ref<DialectCode>('cmn')
  const error = ref<string | null>(null)

  async function sendText(text: string, userId: string): Promise<boolean> {
    if (!text.trim()) return false

    messages.value.push({ role: 'user', content: text })
    isProcessing.value = true
    error.value = null

    try {
      const resp: ChatResponse = await apiChat({
        user_id: userId,
        message: text,
        dialect: dialect.value,
      })
      messages.value.push({ role: 'assistant', content: resp.response })
      return true
    } catch (e: any) {
      error.value = e.message || '发送失败'
      // 失败时把刚 push 的 user 消息撤回，避免 latestUser 误显示
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'user' && last.content === text) {
        messages.value.pop()
      }
      return false
    } finally {
      isProcessing.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    messages,
    isProcessing,
    isRecording,
    isPlaying,
    dialect,
    error,
    sendText,
    clearError,
  }
})
