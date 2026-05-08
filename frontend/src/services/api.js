import axios from 'axios'

// 1. URL'i tek bir yerden, doğru şekilde alıyoruz
const BASE_URL = 'https://reliable-academic-assistant-v2-live.onrender.com';

// 2. 'api' nesnesini SADECE BİR KEZ oluşturuyoruz
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// 3. İsteklere token ekleme mantığı
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 4. Refresh token ve hata yönetimi (api değişkenini tekrar tanımlamadan!)
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(p => (error ? p.reject(error) : p.resolve(token)))
  failedQueue = []
}

api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            original.headers.Authorization = `Bearer ${token}`
            return api(original)
          })
          .catch(e => Promise.reject(e))
      }

      original._retry = true
      isRefreshing = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(err)
      }

      try {
        // Burada axios.post yerine api.post kullanıyoruz
        const { data } = await api.post('/api/auth/refresh', {
          refresh_token: refreshToken,
        })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        
        processQueue(null, data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(err)
  }
)

export default api