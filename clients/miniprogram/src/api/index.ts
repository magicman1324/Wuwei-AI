import { request } from './request'
import { BASE_URL } from '../utils/config'

// ── Health ──

export function healthCheck() {
  return request<{ status: string; service: string }>({ url: '/health' })
}

// ── User ──

export interface UserResponse {
  id: string
  display_name: string
  dialect_preference: string
  tts_speed: number
  tts_volume: number
  font_size: string
}

export function createUser(data: {
  device_id?: string
  display_name?: string
  dialect_preference?: string
}) {
  return request<UserResponse>({ url: '/users', method: 'POST', data })
}

export function getUser(userId: string) {
  return request<UserResponse>({ url: `/users/${userId}` })
}

export function updatePreferences(
  userId: string,
  data: {
    dialect_preference?: string
    tts_speed?: number
    tts_volume?: number
    font_size?: string
  },
) {
  return request<UserResponse>({
    url: `/users/${userId}/preferences`,
    method: 'PATCH',
    data,
  })
}

// ── Chat ──

export interface ChatResponse {
  response: string
  dialect: string
  conversation_id: string | null
}

export function chat(data: {
  user_id: string
  message: string
  dialect?: string
}) {
  return request<ChatResponse>({ url: '/chat', method: 'POST', data })
}

// ── Voice ──

export interface VoiceResponse {
  recognized_text: string
  normalized_text: string
  response_text: string
  dialect_detected: string
  audio_base64: string | null
  audio_format: string
}

// 语音上传需要 uploadFile（multipart），单独处理
export function voiceChat(options: {
  filePath: string
  userId: string
  dialectHint: string
  audioFormat: string
}): Promise<VoiceResponse> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1'}/voice`,
      filePath: options.filePath,
      name: 'audio',
      formData: {
        user_id: options.userId,
        dialect_hint: options.dialectHint,
        audio_format: options.audioFormat,
        sample_rate: '16000',
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data as string) as VoiceResponse)
        } else {
          reject(new Error(`语音上传失败 (${res.statusCode})`))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '语音上传网络错误'))
      },
    })
  })
}

// ── Conversations ──

export interface ConversationSummary {
  id: string
  dialect_used: string
  started_at: string
  message_count: number
}

export interface MessageItem {
  id: string
  role: string
  content: string
  dialect: string
  created_at: string
}

export interface ConversationDetail {
  id: string
  dialect_used: string
  started_at: string
  messages: MessageItem[]
}

export function listConversations(userId: string, limit = 50) {
  return request<ConversationSummary[]>({
    url: `/conversations/${userId}?limit=${limit}`,
  })
}

export function getConversation(userId: string, conversationId: string) {
  return request<ConversationDetail>({
    url: `/conversations/${userId}/${conversationId}`,
  })
}

export function deleteConversation(userId: string, conversationId: string) {
  return request({ url: `/conversations/${userId}/${conversationId}`, method: 'DELETE' })
}

// ── Radio (老年电台) ──

export interface RadioEpisode {
  id: string
  date: string
  category: 'health' | 'nostalgia' | string
  subtopic: string | null
  dialect: string
  title: string
  text: string
  audio_url: string | null
  duration_ms: number
  status: string
  created_at: string
}

export function getRadioToday(dialect = 'cmn') {
  return request<RadioEpisode[]>({ url: `/radio/today?dialect=${dialect}` })
}

export function listRadioEpisodes(days = 14, dialect = 'cmn') {
  return request<RadioEpisode[]>({
    url: `/radio/episodes?days=${days}&dialect=${dialect}`,
  })
}

export function getRadioEpisode(id: string) {
  return request<RadioEpisode>({ url: `/radio/episodes/${id}` })
}

export function radioAudioUrl(id: string): string {
  return `${BASE_URL}/radio/audio/${id}`
}
