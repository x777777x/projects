<template>
  <div class="project-detail-container" v-loading="loading">
    <el-card class="box-card" v-if="projectData">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="$router.push('/files')" icon="Back">返回</el-button>
            <span class="project-title">{{ projectData.project_name }}</span>
          </div>
          <el-button type="success" @click="$router.push(`/projects/${projectData.project_id}/gantt`)">切换到甘特图</el-button>
        </div>
      </template>

      <!-- 概览数据 -->
      <div class="statistics-board">
        <el-row :gutter="20">
          <el-col :span="4">
            <div class="stat-card bg-blue">
              <div class="title">总任务数</div>
              <div class="value">{{ projectData.statistics.total_tasks }}</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-card bg-green">
              <div class="title">已完成</div>
              <div class="value">{{ projectData.statistics.completed_tasks }}</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-card bg-orange">
              <div class="title">进行中</div>
              <div class="value">{{ projectData.statistics.in_progress_tasks }}</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-card bg-purple">
              <div class="title">整体进度</div>
              <div class="value">{{ projectData.statistics.overall_progress.toFixed(1) }}%</div>
            </div>
          </el-col>
        </el-row>
        <div style="margin-top: 15px;">
          <el-progress :percentage="Number(projectData.statistics.overall_progress.toFixed(1))" :stroke-width="15" />
        </div>
      </div>

      <!-- 任务树区域 -->
      <div class="tree-layout">
        <div class="tree-sidebar">
          <h4>项目任务树结构</h4>
          <el-tree
            :data="treeData"
            :props="defaultProps"
            @node-click="handleNodeClick"
            default-expand-all
            highlight-current
            class="task-tree"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <span class="node-label" :class="{ 'text-danger': isTaskOverdue(data.start_date, data.end_date, data.status) }">
                  {{ node.label }}
                  <el-tag size="small" type="danger" v-if="isTaskOverdue(data.start_date, data.end_date, data.status)" style="margin-left: 5px;">超期预警</el-tag>
                </span>
                <el-tag size="small" :type="getStatusType(data.status)" v-if="data.status">
                  {{ data.status }}
                </el-tag>
                <span v-if="data.progress !== undefined" class="node-progress">
                  {{ typeof data.progress === 'number' ? data.progress.toFixed(0) + '%' : '' }}
                </span>
              </span>
            </template>
          </el-tree>
        </div>
        <div class="tree-content">
          <div v-if="selectedNode" class="node-detail">
            <h3>任务详情</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务名称">{{ selectedNode.name }}</el-descriptions-item>
              <el-descriptions-item label="层级">
                <el-tag v-if="selectedNode.type === 'milestone'">里程碑</el-tag>
                <el-tag v-else-if="selectedNode.type === 'level1'" type="success">一级任务</el-tag>
                <el-tag v-else type="warning">二级任务</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ selectedNode.start_date ? selectedNode.start_date.split(' ')[0] : '-' }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ selectedNode.end_date ? selectedNode.end_date.split(' ')[0] : '-' }}</el-descriptions-item>
              <el-descriptions-item label="状态" v-if="selectedNode.status">
                <el-tag :type="getStatusType(selectedNode.status)" style="margin-right: 10px;">{{ selectedNode.status }}</el-tag>
                <el-tag type="danger" v-if="isTaskOverdue(selectedNode.start_date, selectedNode.end_date, selectedNode.status)">超期预警</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="进度">
                <el-progress :percentage="Number(selectedNode.progress?.toFixed(1) || 0)" />
              </el-descriptions-item>
              <el-descriptions-item label="责任部门" v-if="selectedNode.type !== 'milestone'">
                {{ selectedNode.departments?.join(', ') || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="备注" v-if="selectedNode.remarks !== undefined">
                {{ selectedNode.remarks || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="请在左侧点击节点查看详情" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getProjectDetail } from '@/api'
import { isTaskOverdue } from '@/utils/time'

const route = useRoute()
const projectId = route.params.id

const projectData = ref(null)
const loading = ref(false)
const treeData = ref([])
const selectedNode = ref(null)

const defaultProps = {
  children: 'children',
  label: 'name'
}

const getStatusType = (status) => {
  if (status === '已完成') return 'success'
  if (status === '进行中') return 'warning'
  return 'info'
}

const buildTreeData = (milestones) => {
  return milestones.map(ms => {
    return {
      ...ms,
      type: 'milestone',
      status: ms.progress === 100 ? '已完成' : (ms.progress > 0 ? '进行中' : '未开始'),
      children: ms.tasks_level1.map(l1 => {
        return {
          ...l1,
          type: 'level1',
          children: l1.tasks_level2?.map(l2 => ({
            ...l2,
            type: 'level2'
          })) || []
        }
      })
    }
  })
}

const handleNodeClick = (data) => {
  selectedNode.value = data
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await getProjectDetail(projectId)
    projectData.value = data
    treeData.value = buildTreeData(data.milestones || [])
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.project-detail-container {
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
.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}
.project-title {
  font-size: 18px;
  font-weight: bold;
}
.statistics-board {
  margin-bottom: 30px;
}
.stat-card {
  padding: 15px;
  border-radius: 8px;
  color: white;
  text-align: center;
}
.bg-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.bg-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.bg-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
.bg-purple { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
.stat-card .title { font-size: 14px; margin-bottom: 5px; opacity: 0.9; }
.stat-card .value { font-size: 24px; font-weight: bold; }

.tree-layout {
  display: flex;
  min-height: 500px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.tree-sidebar {
  width: 40%;
  border-right: 1px solid #ebeef5;
  padding: 15px;
  overflow-y: auto;
  background-color: #fafafa;
}
.tree-sidebar h4 {
  margin-top: 0;
  margin-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}
.tree-content {
  width: 60%;
  padding: 20px;
  overflow-y: auto;
}
.task-tree {
  background-color: transparent;
}
.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}
.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 10px;
}
.text-danger {
  color: #f56c6c !important;
}
.node-progress {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}
</style>
