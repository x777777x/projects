<template>
  <div class="file-list-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>项目列表</span>
          <div>
            <el-button type="success" @click="$router.push('/gantt/all')" style="margin-right: 10px;">全局进度大屏</el-button>
            <el-button @click="showTemplateDialog = true" style="margin-right: 10px;">下载模板</el-button>
            <el-button type="primary" @click="handleUploadClick">上传新项目</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="projects" style="width: 100%" v-loading="loading">
        <el-table-column prop="project_name" label="项目名称" width="200" />
        <el-table-column prop="start_date" label="项目开始" width="110">
          <template #default="scope">
            {{ scope.row.start_date ? scope.row.start_date.split(' ')[0] : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="end_date" label="项目结束" width="110">
          <template #default="scope">
            {{ scope.row.end_date ? scope.row.end_date.split(' ')[0] : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="task_count" label="任务总数" width="90" />
        <el-table-column prop="completed_tasks" label="已完成" width="80" />
        <el-table-column prop="in_progress_tasks" label="进行中" width="80" />
        <el-table-column prop="unstarted_tasks" label="未开始" width="80" />
        <el-table-column label="整体进度" width="200">
          <template #default="scope">
            <el-progress :percentage="Number(scope.row.overall_progress.toFixed(1))" />
          </template>
        </el-table-column>
        <el-table-column prop="warning_count" label="格式预警" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.warning_count > 0 ? 'warning' : 'success'">
              {{ scope.row.warning_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overdue_count" label="进度预警" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.overdue_count > 0 ? 'danger' : 'success'">
              {{ scope.row.overdue_count }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" min-width="320">
          <template #default="scope">
            <el-button size="small" type="info" @click="handleFileInfo(scope.row)">文件信息</el-button>
            <el-button size="small" @click="goToDetail(scope.row)">查看结构</el-button>
            <el-button size="small" type="success" @click="goToGantt(scope.row)">甘特图</el-button>
            <el-button size="small" type="danger" @click="handleDeleteClick(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 下载模板提示弹窗 -->
    <el-dialog v-model="showTemplateDialog" title="模板下载与填写指南" width="60%">
      <div class="template-instructions">
        <h3>项目信息表填写要求：</h3>
        <ol>
          <li><strong>项目名称：</strong>第一行必须是项目名称。</li>
          <li><strong>表头规范：</strong>第二行为列头，必须严格按照以下顺序和名称：编号、里程碑、一级任务、二级任务、责任部门、工期、开始时间、结束时间、状态、备注。</li>
          <li><strong>编号要求：</strong>第一列编号序号必须连续、无重复、无遗漏。</li>
          <li><strong>状态规范：</strong>状态列中的值只能是“未开始”、“进行中”或“已完成”。</li>
          <li><strong>时间格式：</strong>开始时间和结束时间需在“设置单元格格式”中设置为“日期”类型格式“2000-01-01”。</li>
          <li><strong>工期规范：</strong>工期必须为整型数字。</li>
        </ol>
        <p class="warning-text"><el-icon><Warning /></el-icon> 如果不符合以上任一要求，系统将在上传时校验失败并提示具体错误。</p>
        <div class="download-action">
          <el-button type="primary" @click="downloadTemplate">立即下载模板(XLSX)</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 文件信息弹窗 -->
    <el-dialog v-model="showFileInfoDialog" title="文件信息" width="40%">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="原始文件名">{{ currentFileInfo.display_name }}</el-descriptions-item>
        <el-descriptions-item label="上传时间">{{ currentFileInfo.upload_time }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="success" @click="downloadOriginalFile(currentFileInfo.project_id)" :loading="downloading">下载原始文件</el-button>
          <el-button type="primary" @click="showFileInfoDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 密码校验弹窗 -->
    <el-dialog v-model="showPwdDialog" title="安全校验" width="400px" @close="resetPwdForm">
      <el-form @submit.prevent>
        <el-form-item label="管理员密码">
          <el-input 
            v-model="adminPwd" 
            type="password" 
            show-password 
            placeholder="请输入管理员密码" 
            @keyup.enter="verifyAndProceed"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPwdDialog = false">取消</el-button>
          <el-button type="primary" @click="verifyAndProceed" :loading="verifying">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFiles, deleteFile, verifyPassword, downloadOriginalFileApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const showTemplateDialog = ref(false)

// 文件信息弹窗相关
const showFileInfoDialog = ref(false)
const currentFileInfo = ref({})
const downloading = ref(false)

// 密码校验相关
const showPwdDialog = ref(false)
const adminPwd = ref('')
const verifying = ref(false)
const pendingAction = ref(null) // 'upload' 或 { type: 'delete', row: Object }


const downloadTemplate = () => {
  const link = document.createElement('a')
  link.href = '/项目模板.xlsx'
  link.setAttribute('download', '项目模板.xlsx')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showTemplateDialog.value = false
}

const loadProjects = async () => {
  loading.value = true
  try {
    const data = await getFiles()
    projects.value = data || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const goToDetail = (row) => {
  router.push(`/projects/${row.project_id}/detail`)
}

const goToGantt = (row) => {
  router.push(`/projects/${row.project_id}/gantt`)
}

const handleFileInfo = (row) => {
  currentFileInfo.value = {
    project_id: row.project_id,
    display_name: row.display_name,
    upload_time: row.upload_time
  }
  showFileInfoDialog.value = true
}

const downloadOriginalFile = async (projectId) => {
  if (!projectId) return
  downloading.value = true
  try {
    const blob = await downloadOriginalFileApi(projectId)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', currentFileInfo.value.display_name || 'project_file.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('文件下载失败')
  } finally {
    downloading.value = false
  }
}

const handleUploadClick = () => {
  const savedPwd = localStorage.getItem('admin_pwd')
  if (savedPwd) {
    router.push('/upload')
  } else {
    pendingAction.value = 'upload'
    showPwdDialog.value = true
  }
}

const handleDeleteClick = (row) => {
  ElMessageBox.confirm(
    '确定要删除这个项目吗？此操作不可逆。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    const savedPwd = localStorage.getItem('admin_pwd')
    if (savedPwd) {
      executeDelete(row)
    } else {
      pendingAction.value = { type: 'delete', row }
      showPwdDialog.value = true
    }
  }).catch(() => {})
}

const executeDelete = async (row) => {
  try {
    await deleteFile(row.project_id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (error) {
    console.error(error)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('admin_pwd')
      ElMessage.error('密码已失效，请重新输入')
    }
  }
}

const verifyAndProceed = async () => {
  if (!adminPwd.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  verifying.value = true
  try {
    await verifyPassword(adminPwd.value)
    // 校验通过，存入本地
    localStorage.setItem('admin_pwd', adminPwd.value)
    showPwdDialog.value = false
    
    // 继续执行被拦截的动作
    if (pendingAction.value === 'upload') {
      router.push('/upload')
    } else if (pendingAction.value && pendingAction.value.type === 'delete') {
      executeDelete(pendingAction.value.row)
    }
  } catch (error) {
    console.error(error)
  } finally {
    verifying.value = false
  }
}

const resetPwdForm = () => {
  adminPwd.value = ''
  pendingAction.value = null
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.file-list-container {
  padding: 20px;
  width: 90%;
  max-width: none;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.template-instructions h3 {
  margin-top: 0;
  color: #303133;
}
.template-instructions ol {
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}
.warning-text {
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 15px;
}
.download-action {
  margin-top: 25px;
  text-align: center;
}
</style>
