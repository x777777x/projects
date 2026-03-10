<template>
  <div class="gantt-container" v-loading="loading">
    <el-card class="box-card gantt-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="$router.push('/files')" icon="Back">返回列表</el-button>
            <el-button @click="$router.push(`/projects/${projectId}/detail`)">项目结构</el-button>
            <span class="project-title">{{ projectName }} - 甘特图</span>
          </div>
          <div class="header-right">
            <el-radio-group v-model="ganttScale" size="small" @change="changeGanttScale">
              <el-radio-button label="day">日视图</el-radio-button>
              <el-radio-button label="week">周视图</el-radio-button>
              <el-radio-button label="month">月视图</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-controls">
        <el-input v-model="filters.keyword" placeholder="搜索任务名称..." style="width: 200px" clearable @input="applyFilters" />
        <el-select v-model="filters.status" placeholder="状态筛选" style="width: 150px" clearable @change="applyFilters">
          <el-option label="未开始" value="未开始" />
          <el-option label="进行中" value="进行中" />
          <el-option label="已完成" value="已完成" />
        </el-select>
        <el-select v-model="filters.department" placeholder="部门筛选" style="width: 150px" clearable @change="applyFilters">
          <el-option v-for="dept in allDepartments" :key="dept" :label="dept" :value="dept" />
        </el-select>
        <el-button type="primary" @click="resetFilters">重置</el-button>
        <el-checkbox v-model="showDetailedCols" @change="updateColumns" style="margin-left: 20px;">显示里程碑及一级任务</el-checkbox>
        </div>
        <div class="color-legend">
          <span class="legend-item"><span class="color-dot" style="background: #67c23a;"></span>已完成</span>
          <span class="legend-item"><span class="color-dot" style="background: #e6a23c;"></span>进行中</span>
          <span class="legend-item"><span class="color-dot" style="background: #909399;"></span>未开始</span>
          <span class="legend-item"><span class="color-dot" style="background: #f56c6c;"></span>延期/超期</span>
        </div>
      </div>

      <!-- 甘特图内容区 -->
      <div ref="ganttContainer" class="gantt-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getProjectGantt } from '@/api'
import { isTaskOverdue } from '@/utils/time'
import gantt from 'dhtmlx-gantt'
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'

const route = useRoute()
const projectId = route.params.id

const loading = ref(false)
const projectName = ref('')
const rawTasks = ref([])
const allDepartments = ref([])
const ganttContainer = ref(null)

const ganttScale = ref('day')

const filters = reactive({
  keyword: '',
  status: '',
  department: ''
})

const showDetailedCols = ref(false)

const changeGanttScale = (val) => {
  if (val === 'day') {
    gantt.config.scale_unit = 'day';
    gantt.config.date_scale = '%m-%d';
    gantt.config.subscales = [];
  } else if (val === 'week') {
    gantt.config.scale_unit = 'week';
    gantt.config.date_scale = '第%W周';
    gantt.config.subscales = [{ unit: 'day', step: 1, date: '%D' }];
  } else if (val === 'month') {
    gantt.config.scale_unit = 'month';
    gantt.config.date_scale = '%Y年%m月';
    gantt.config.subscales = [{ unit: 'week', step: 1, date: '第%W周' }];
  }
  gantt.render();
}

const applyFilters = () => {
  gantt.render()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.department = ''
  applyFilters()
}

// dhtmlx 初始化
const updateColumns = () => {
  const baseCols = [];

  if (showDetailedCols.value) {
    baseCols.push({ name: "milestone", label: "里程碑", align: "center", width: 100 });
    baseCols.push({ name: "level1", label: "一级任务", align: "center", width: 100 });
  }

  baseCols.push({ 
    name: "text", 
    label: "任务名称", 
    width: 250, 
    tree: true,
    template: (task) => {
      let html = `<span>${task.text}</span>`;
      if (isTaskOverdue(task.start_date_raw, task.end_date_raw, task.status)) {
        html += `<span style="color: #fff; background-color: #f56c6c; padding: 2px 4px; border-radius: 4px; font-size: 10px; margin-left: 6px;">超期预警</span>`;
      }
      return html;
    }
  });

  baseCols.push(
    { name: "start_date", label: "开始", align: "center", width: 90 },
    { name: "end_date", label: "结束", align: "center", width: 90 },
    { name: "departments", label: "部门", align: "center", width: 100, template: obj => obj.departments?.join(',') || '-' },
    { name: "status", label: "状态", align: "center", width: 70 }
  );

  gantt.config.columns = baseCols;
  gantt.render();
}

const initGantt = () => {
  gantt.config.readonly = true;
  gantt.config.date_format = "%Y-%m-%d"; // 配置 dhtmlx-gantt 解析日期的格式
  
  // 启用拓展包 Tooltip
  gantt.plugins({ tooltip: true });

  updateColumns();

  // 自定义 浮窗(Tooltip) 的内容
  gantt.templates.tooltip_text = function(start, end, task) {
      const st = start ? gantt.date.date_to_str("%Y-%m-%d")(start) : "-";
      const et = end ? gantt.date.date_to_str("%Y-%m-%d")(end) : "-";
      const rm = task.remark ? task.remark : "无";
      const ms = task.milestone ? `<b>里程碑：</b> ${task.milestone}<br/>` : "";
      const l1 = task.level1 ? `<b>一级任务：</b> ${task.level1}<br/>` : "";
      
      return ms + l1 +
             `<b>二级任务：</b> ${task.text}<br/>` +
             `<b>状态：</b> ${task.status}<br/>` +
             `<b>开始时间：</b> ${st}<br/>` +
             `<b>结束时间：</b> ${et}<br/>` +
             `<b>备注：</b> ${rm}`;
  };

  gantt.templates.task_class = (start, end, task) => {
    // 动态校验是否超期
    if (isTaskOverdue(task.start_date_raw, task.end_date_raw, task.status)) {
      return 'gantt_task_overdue';
    }
    if (task.status === '已完成') return 'gantt_task_completed';
    if (task.status === '进行中') return 'gantt_task_progress';
    return 'gantt_task_waiting';
  };

  // 过滤逻辑
  gantt.attachEvent("onBeforeTaskDisplay", (id, task) => {
    if (filters.keyword && !task.text.toLowerCase().includes(filters.keyword.toLowerCase())) return false;
    if (filters.status && task.status !== filters.status) return false;
    if (filters.department && (!task.departments || !task.departments.includes(filters.department))) return false;
    return true;
  });

  gantt.init(ganttContainer.value);
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await getProjectGantt(projectId)
    projectName.value = data.project_name
    rawTasks.value = data.tasks || []
    
    // 提取所有部门供筛选
    const depts = new Set()
    rawTasks.value.forEach(t => {
      if (t.departments) {
        t.departments.forEach(d => depts.add(d))
      }
    })
    allDepartments.value = Array.from(depts)

    // 格式化数据给 gantt
    // 注意：原本后端传来的 gantt 我们没处理 parent ID，为了让 dhtmlx 支持树形展示，
    // 我们需要基于 milestone 和 level1 虚拟出层级结构 (简单扁平展示也可以)。
    // 这里为了简单，直接扁平展示所有任务。如果需要树形，可以根据 milestone 生成虚拟父节点。
    
    // 简化处理：将所有任务作为一级节点平铺
    const ganttData = {
      data: rawTasks.value.map(t => {
        return {
          id: t.id,
          text: t.name,
          start_date: t.start || null, 
          end_date: t.end || null, // 显式传递结束时间
          duration: t.start && t.end ? 
            Math.ceil((new Date(t.end) - new Date(t.start))/(1000*60*60*24)) + 1 
            : 1,
          progress: (t.progress || 0) / 100,
          status: t.status,
          departments: t.departments,
          start_date_raw: t.start, // 保留原始字符串用于超期对比
          end_date_raw: t.end,
          milestone: t.milestone || '',
          level1: t.parent_task || ''
        }
      }).filter(t => t.start_date) // 没有具体时间的无法渲染甘特图
    }

    initGantt()
    gantt.parse(ganttData)

  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  gantt.clearAll()
})
</script>

<style>
.gantt-container {
  padding: 20px;
  height: calc(100vh - 40px);
  box-sizing: border-box;
}
.gantt-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.gantt-card .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
  overflow: hidden;
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
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.filter-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}
.color-legend {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #606266;
}
.legend-item {
  display: flex;
  align-items: center;
}
.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
}
.gantt-chart {
  flex: 1;
  width: 100%;
  min-height: 400px;
}

/* 隐藏所有的默认文字，保持画面整洁，统一采用浮窗 */
.gantt_task_content {
   color: transparent !important; 
}

/* 强制清除所有甘特条默认的最外层容器边框（防止透出 dhtmlx 自身的绿色或其他状态色） */
.gantt_task_line {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* 保证进度块带圆角和确切的边框 */
.gantt_task_content, .gantt_task_progress {
    border-radius: 4px;
}

/* 自定义甘特图颜色 */
.gantt_task_completed .gantt_task_content { background: #67c23a !important; border: 0px solid #5daf34 !important; }
.gantt_task_progress .gantt_task_content { background: #e6a23c !important; border: 0px solid #cf9236 !important; }
.gantt_task_waiting .gantt_task_content { background: #909399 !important; border: 0px solid #82848a !important; }
.gantt_task_overdue .gantt_task_content { background: #f56c6c !important; border: 0px solid #e35555 !important; }

/* 浮窗拓展配置 */
.gantt_tooltip {
    font-size: 13px !important;
    color: #333 !important;
    z-index: 10000;
}
</style>
