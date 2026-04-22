// 开发环境用本地后端，生产环境替换为线上地址
export const BASE_URL = 'http://127.0.0.1:8000/api/v1'
export const WS_URL = 'ws://127.0.0.1:8000/api/v1/ws/voice-stream'

export const DIALECTS = [
  { code: 'cmn', label: '普通话' },
  { code: 'yue', label: '粤语' },
  { code: 'cmn-sichuan', label: '四川话' },
] as const

export type DialectCode = typeof DIALECTS[number]['code']
