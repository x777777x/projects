<template>
  <div class="upload-container" style="width: 60%;">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>上传项目进度表</span>
          <el-button @click="$router.push('/files')">返回列表</el-button>
        </div>
      </template>

      <el-upload
        class="upload-demo"
        drag
        action="#"
        :http-request="customUpload"
        :show-file-list="false"
        accept=".xlsx, .xls"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 xlsx/xls 文件，且不超过 50MB。请确保文件格式符合规范。<br>
            项目名称不能重复，如需要更新项目信息，可以从项目列表下载原文件进行修改，在删除原文件后重新上传。<br>
          </div>
        </template>
      </el-upload>

      <!-- 上传结果展示区 -->
      <div v-if="uploadResult" class="result-area">
        <el-alert
          v-if="uploadResult.success"
          title="上传并解析成功"
          type="success"
          show-icon
          :closable="false"
        />
        <el-alert
          v-else
          title="文件解析失败"
          type="error"
          show-icon
          :closable="false"
        />

        <div v-if="uploadResult.warnings && uploadResult.warnings.length" class="message-list warning-list">
          <h4><el-icon><Warning /></el-icon> 格式预警 ({{ uploadResult.warnings.length }})</h4>
          <ul>
            <li v-for="(warn, index) in uploadResult.warnings" :key="'w'+index">{{ warn }}</li>
          </ul>
        </div>

        <div v-if="uploadResult.errors && uploadResult.errors.length" class="message-list error-list">
          <h4><el-icon><CircleClose /></el-icon> 错误列表 ({{ uploadResult.errors.length }})</h4>
          <ul>
            <li v-for="(err, index) in uploadResult.errors" :key="'e'+index">{{ err }}</li>
          </ul>
        </div>

        <div class="actions" v-if="uploadResult.success">
          <el-button type="primary" @click="$router.push(`/projects/${uploadResult.project_id}/detail`)">查看项目结构</el-button>
          <el-button type="success" @click="$router.push(`/projects/${uploadResult.project_id}/gantt`)">查看甘特图</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled, Warning, CircleClose } from '@element-plus/icons-vue'
import { uploadFile } from '@/api'
import { ElMessage } from 'element-plus'

const uploadResult = ref(null)

const customUpload = async (options) => {
  const { file } = options
  
  // 校验文件大小 (50MB)
  if (file.size / 1024 / 1024 > 50) {
    ElMessage.error('文件大小不能超过 50MB!')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  try {
    uploadResult.value = null
    const res = await uploadFile(formData)
    uploadResult.value = {
      success: true,
      project_id: res.project_id,
      warnings: res.warnings || [],
      errors: []
    }
    ElMessage.success('上传成功')
  } catch (error) {
    uploadResult.value = {
      success: false,
      errors: error.errors || [error.detail || '未知错误'],
      warnings: error.warnings || []
    }
  }
}
</script>

<style scoped>
.upload-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-area {
  margin-top: 30px;
}
.message-list {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
}
.message-list h4 {
  margin-top: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}
.warning-list {
  background-color: #fdf6ec;
  color: #e6a23c;
}
.error-list {
  background-color: #fef0f0;
  color: #f56c6c;
}
.message-list ul {
  padding-left: 20px;
  margin-bottom: 0;
}
.actions {
  margin-top: 20px;
  display: flex;
  gap: 15px;
  justify-content: center;
}
</style>
