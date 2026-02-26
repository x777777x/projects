import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        redirect: '/files'
    },
    {
        path: '/files',
        name: 'FileList',
        component: () => import('@/views/FileList.vue')
    },
    {
        path: '/upload',
        name: 'Upload',
        component: () => import('@/views/UploadView.vue')
    },
    {
        path: '/projects/:id/detail',
        name: 'ProjectDetail',
        component: () => import('@/views/ProjectDetail.vue')
    },
    {
        path: '/projects/:id/gantt',
        name: 'ProjectGantt',
        component: () => import('@/views/ProjectGantt.vue')
    },
    {
        path: '/gantt/all',
        name: 'AllProjectsGantt',
        component: () => import('@/views/AllProjectsGantt.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
