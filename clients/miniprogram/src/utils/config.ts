// ========== 环境切换 ==========
// 模拟器开发：       env = 'local'
// 真机调试(ngrok)：  env = 'tunnel'，填入 ngrok 给的域名
// 正式部署：         env = 'prod'，填入服务器域名
const env: 'local' | 'tunnel' | 'prod' = 'local'

const HOSTS: Record<typeof env, { http: string; ws: string }> = {
  local: {
    http: 'http://127.0.0.1:8000',
    ws: 'ws://127.0.0.1:8000',
  },
  tunnel: {
    // ngrok/cpolar 隧道地址（真机调试用）
    // 运行 ngrok http 8000 后把域名填到这里
    http: 'https://YOUR-TUNNEL.ngrok-free.app',
    ws: 'wss://YOUR-TUNNEL.ngrok-free.app',
  },
  prod: {
    http: 'https://your-server.com',
    ws: 'wss://your-server.com',
  },
}

export const BASE_URL = `${HOSTS[env].http}/api/v1`
export const WS_URL = `${HOSTS[env].ws}/api/v1/ws/voice-stream`

export const DIALECTS = [
  { code: 'cmn', label: '普通话' },
  { code: 'yue', label: '粤语' },
  { code: 'cmn-sichuan', label: '四川话' },
] as const

export type DialectCode = typeof DIALECTS[number]['code']
