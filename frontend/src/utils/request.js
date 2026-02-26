import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
    baseURL: '/api',
    timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
    (config) => {
        const pwd = localStorage.getItem('admin_pwd')
        if (pwd) {
            config.headers['x-admin-password'] = pwd
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
request.interceptors.response.use(
    (response) => {
        return response.data
    },
    (error) => {
        if (error.response && error.response.data && error.response.data.detail) {
            ElMessage.error(error.response.data.detail)
        } else if (error.response && error.response.data && error.response.data.errors) {
            // 特殊处理带有 errors 列表的情况
            return Promise.reject(error.response.data)
        } else {
            ElMessage.error('请求失败，请稍后重试')
        }
        return Promise.reject(error)
    }
)

export default request
