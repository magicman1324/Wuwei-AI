import { BASE_URL } from '../utils/config'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  data?: Record<string, any>
  header?: Record<string, string>
  timeout?: number
}

interface ApiResponse<T = any> {
  data: T
  statusCode: number
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...options.header,
      },
      timeout: options.timeout || 15000,
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          const detail = res.data?.detail || `请求失败 (${res.statusCode})`
          reject(new Error(detail))
        }
      },
      fail: (err: any) => {
        reject(new Error(err.errMsg || '网络错误，请检查网络连接'))
      },
    })
  })
}
