import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 仅在开发环境输出API地址
if (process.env.NODE_ENV === 'development') {
  console.log('🌐 API Base URL:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 仅在开发环境且启用调试时输出详细请求信息
    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true') {
      console.log('🌐 API 请求:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        fullURL: `${config.baseURL}${config.url}`,
      });
    }
    
    // 添加认证token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
      if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true') {
        console.log('🔑 添加 Token');
      }
    }
    
    // 添加CSRF保护
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    console.error('🚫 API 请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // 仅在开发环境且启用调试时输出响应信息
    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true') {
      console.log('✅ API 响应:', {
        status: response.status,
        url: response.config.url,
      });
    }
    return response;
  },
  (error: AxiosError) => {
    // 仅在开发环境或发生错误时输出错误信息
    if (process.env.NODE_ENV === 'development') {
      console.error('❌ API 响应错误:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        url: error.config?.url
      });
    }
    
    const { response } = error;
    
    if (response) {
      switch (response.status) {
        case 401:
          // 未认证，清除token
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          if (process.env.NODE_ENV === 'development') {
            console.warn('🔑 Token 已过期，清除本地存储');
          }
          break;
        case 403:
          if (process.env.NODE_ENV === 'development') {
            console.warn('🚫 权限不足');
          }
          break;
        case 404:
          if (process.env.NODE_ENV === 'development') {
            console.warn('❓ 资源不存在');
          }
          break;
        case 500:
          console.error('💥 服务器内部错误');
          break;
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('⏰ 请求超时');
    } else {
      console.error('🌐 网络错误');
    }
    
    return Promise.reject(error);
  }
);

export default api;
