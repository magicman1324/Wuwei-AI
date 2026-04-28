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

  async function sendText(text: string, userId: string) {
    if (!text.trim()) return

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
    } catch (e: any) {
      error.value = e.message || '发送失败'
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
