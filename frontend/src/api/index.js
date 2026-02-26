import request from '@/utils/request'

export const verifyPassword = (password) => {
    return request({
        url: '/files/verify-pwd',
        method: 'post',
        data: { password }
    })
}

export const uploadFile = (data) => {
    return request({
        url: '/files/upload',
        method: 'post',
        data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export const getFiles = () => {
    return request({
        url: '/files',
        method: 'get'
    })
}

export const deleteFile = (projectId) => {
    return request({
        url: `/files/${projectId}`,
        method: 'delete'
    })
}

export const getProjectDetail = (projectId) => {
    return request({
        url: `/projects/${projectId}/detail`,
        method: 'get'
    })
}

export const getProjectGantt = (projectId) => {
    return request({
        url: `/projects/${projectId}/gantt`,
        method: 'get'
    })
}

export const getAllProjectsGantt = () => {
    return request({
        url: `/projects/all/gantt`,
        method: 'get'
    })
}
