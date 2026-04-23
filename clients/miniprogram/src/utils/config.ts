// 真机调试用电脑局域网 IP，开发者工具模拟器用 127.0.0.1
export const BASE_URL = 'http://192.168.42.1:8000/api/v1'
export const WS_URL = 'ws://192.168.42.1:8000/api/v1/ws/voice-stream'

export const DIALECTS = [
  { code: 'cmn', label: '普通话' },
  { code: 'yue', label: '粤语' },
  { code: 'cmn-sichuan', label: '四川话' },
] as const

export type DialectCode = typeof DIALECTS[number]['code']
