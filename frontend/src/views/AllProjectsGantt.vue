<template>
  <div class="all-gantt-container" v-loading="loading">
    <el-card class="box-card gantt-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="$router.push('/files')" icon="Back">返回列表</el-button>
            <span class="project-title">全部项目进度大屏</span>
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

      <!-- 筛选与图例栏 -->
      <div class="filter-bar">
        <div class="filter-controls">
          <el-input v-model="filters.keyword" placeholder="搜索项目名称..." style="width: 250px" clearable @input="applyFilters" />
          <el-checkbox v-model="showDetailedCols" @change="updateColumns" style="margin-left: 20px;">显示里程碑及一级任务</el-checkbox>
        </div>
        <div class="color-legend">
          <span class="legend-item"><span class="color-dot" style="background: #67c23a;"></span>已完成</span>
          <span class="legend-item"><span class="color-dot" style="background: #e6a23c;"></span>进行中</span>
          <span class="legend-item"><span class="color-dot" style="background: #909399;"></span>未开始</span>
          <span class="legend-item"><span class="color-dot" style="background: #f56c6c;"></span>超期</span>
        </div>
      </div>

      <!-- 甘特图内容区 -->
      <div ref="ganttContainer" class="gantt-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getAllProjectsGantt } from '@/api'
import { isTaskOverdue } from '@/utils/time'
import gantt from 'dhtmlx-gantt'
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'
// Tooltip 所需扩展插件 (大部分老版本内嵌，新版本通过 gantt.plugins 启用)

const router = useRouter()
const loading = ref(false)
const rawProjects = ref([])
const ganttContainer = ref(null)

const ganttScale = ref('month')

const filters = reactive({
  keyword: ''
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

// dhtmlx 初始化
const updateColumns = () => {
  const baseCols = [];
  if (showDetailedCols.value) {
    baseCols.push({ name: "milestone", label: "里程碑", align: "center", width: 100 });
    baseCols.push({ name: "level1", label: "一级任务", align: "center", width: 100 });
  }
  
  baseCols.push(
    { name: "text", label: "项目名称", width: 280, tree: true, template: obj => `<strong>${obj.text}</strong>` },
    { name: "start_date", label: "开始", align: "center", width: 90 },
    { name: "end_date", label: "结束", align: "center", width: 90 },
    { name: "task_count", label: "任务总数", align: "center", width: 80, template: obj => obj.task_count || '' },
    { name: "status", label: "状态", align: "center", width: 70 }
  );
  
  gantt.config.columns = baseCols;
  gantt.render();
}

// 基于 project_id 产生一致的高饱和 HSL 颜色
const getColorByString = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 90%, 35%)`;
};

const calcOverallStatus = (progress, overdue_count, in_progress_tasks, completed_tasks) => {
  if (overdue_count > 0) return '超期';
  if (progress >= 100) return '已完成';
  if (progress > 0 || in_progress_tasks > 0 || completed_tasks > 0) return '进行中';
  return '未开始';
};

const calculateDynamicProgress = (startStr, endStr, progressValue) => {
    // 项目级别的甘特图进度，我们不再按当天时间算比例。
    // 因为项目里不仅有流逝时间，还有真实的工作完成率。
    // 但是用户要求动态涂色以区分进度，我们依然拿传来的 overall_progress 计算。
    return (progressValue || 0) / 100;
};


const initGantt = () => {
  gantt.clearAll();
  gantt.config.readonly = true;
  gantt.config.date_format = "%Y-%m-%d";
  
  // 启用拓展包 Tooltip
  gantt.plugins({ tooltip: true });

  // 默认使用月视图
  gantt.config.scale_unit = 'month';
  gantt.config.date_scale = '%Y年%m月';
  gantt.config.subscales = [{ unit: 'week', step: 1, date: '第%W周' }];

  // 每行的高度稍微调大一点适应外边框
  gantt.config.row_height = 40;
  gantt.config.task_height = 24;

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
    let classes = [];
    let renderingStatus = task.status;

    // 根据动态真实结果重写渲染状态，但不覆盖界面的原文本
    if (task.type === 'task') {
        if (isTaskOverdue(task.start_date_raw, task.end_date_raw, task.status)) {
            renderingStatus = '超期';
        }
    }

    if (task.type === 'task') {
        classes.push('all_gantt_sub_task');
        if (renderingStatus === '超期') classes.push('sub_task_overdue');
        else if (renderingStatus === '已完成') classes.push('sub_task_completed');
        else if (renderingStatus === '进行中') classes.push('sub_task_progress');
        else classes.push('sub_task_waiting');
    } else {
        classes.push('all_gantt_project_task');
        if (renderingStatus === '超期') classes.push('project_overdue');
        else if (renderingStatus === '已完成') classes.push('project_completed');
        else if (renderingStatus === '进行中') classes.push('project_progress');
        else classes.push('project_waiting');
    }
    return classes.join(' ');
  };
  
  gantt.templates.task_row_class = (start, end, task) => {
    return '';
  }
  
  gantt.attachEvent("onTaskDblClick", function(id, e){
    const task = gantt.getTask(id);
    if(task && task.type === 'project') {
      router.push(`/projects/${id}/detail`);
    }
    return false; // 阻止默认的弹框行为
  });

  gantt.attachEvent("onBeforeTaskDisplay", (id, task) => {
    if (filters.keyword && !task.text.toLowerCase().includes(filters.keyword.toLowerCase())) return false;
    return true;
  });
  
  // 由于主项目不显示条形图，我们不再需要在此处加边框
  // gantt.attachEvent("onGanttRender", function(){
  //     // applyCustomBorders();
  // });

  gantt.init(ganttContainer.value);
}

const loadGanttData = async () => {
  loading.value = true
  try {
    const data = await getAllProjectsGantt()
    
    // 直接使用后端打平封装好的含有 children 的结构
    const mappedData = data.map(p => {
        let start = p.start_date ? p.start_date.split(' ')[0] : null;
        let end = p.end_date ? p.end_date.split(' ')[0] : null;

        // 这里后端传过来的数据有 tasks_count 但是可能没带过 in_progress_tasks 到大屏结构里
        // 为了确保能识别 "只有子任务在进行中或已完成" 的状态，我们自己再扫一遍它底下的子任务。
        let subInProgress = 0;
        let subCompleted = 0;
        let subOverdue = 0;

        if (p.children) {
            p.children.forEach(t => {
                 // 必须在这儿先把属于任务真实的动态逾期结果算出来
                 let actualStatus = t.status;
                 if (isTaskOverdue(t.start_date, t.end_date, t.status)) {
                     actualStatus = '超期';
                 }

                 if (actualStatus === '进行中') subInProgress++;
                 else if (actualStatus === '已完成') subCompleted++;
                 else if (actualStatus === '超期') subOverdue++;
            });
        }

        // 把动态统计出的子任务超期情况综合进总超期判断
        const finalOverdueCount = p.overdue_count + subOverdue;

        const pStatus = calcOverallStatus(p.overall_progress, finalOverdueCount, subInProgress, subCompleted);

        return {
          id: p.id,
          text: p.text,
          start_date: start, 
          end_date: end,
          duration: start && end ? 
            Math.ceil((new Date(end) - new Date(start))/(1000*60*60*24)) + 1 
            : 1,
          progress: calculateDynamicProgress(p.start_date, p.end_date, p.overall_progress),
          status: pStatus,
          type: "project",
          task_count: p.task_count,
          borderColor: getColorByString(p.id),
          open: true, // 默认展开子项目
          children: (p.children || []).map(t => {
              // 注意：此时不再修改 t.status 原始字段的值，直接传下去，
              // 留给 task_class 在界面绘画时利用 start_date_raw 和 end_date_raw 动态校验
              return {
                  ...t,
                  duration: t.start_date && t.end_date ? 
                    Math.ceil((new Date(t.end_date) - new Date(t.start_date))/(1000*60*60*24)) + 1 : 1,
                  parent: p.id,
                  type: "task",
                  start_date_raw: t.start_date,
                  end_date_raw: t.end_date,
                  milestone: t.milestone || '',
                  level1: t.level1 || ''
              }
          })
        }
      }).filter(p => p.start_date)

    const flattenData = [];
    mappedData.forEach(p => {
        flattenData.push(p);
        if (p.children && p.children.length > 0) {
            flattenData.push(...p.children);
        }
    });

    const ganttData = {
      data: flattenData
    }

    initGantt()
    gantt.parse(ganttData)
    
    // 由于不再显示主条形图，不用再次调用强制加框
    // nextTick(() => {
    //     applyCustomBorders();
    // })

  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const applyCustomBorders = () => {
    // 仅给"项目"自身上边框
    const tasks = gantt.getTaskByTime();
    tasks.forEach(task => {
        if (task.type === 'project') {
            const domEnv = gantt.getTaskNode(task.id);
            if (domEnv) {
                domEnv.style.border = `2px solid ${task.borderColor}`;
                domEnv.style.boxShadow = `0 1px 4px ${task.borderColor}40`;
                domEnv.style.borderRadius = `6px`;
            }
        }
    });
}

onMounted(() => {
  loadGanttData();
});

onBeforeUnmount(() => {
  gantt.clearAll()
});
</script>

<style>
.all-gantt-container {
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

/* 隐藏所有的默认文字，保持画面整洁 */
.gantt_task_content {
   color: transparent !important; 
}

/* 核心修复：重置和固定基础涂层，避免默认样式串色 */
.all_gantt_project_task .gantt_task_content, 
.all_gantt_sub_task .gantt_task_content {
    border-radius: 4px;
}

/* ================= 隐藏主项目进度条 ================= */
.all_gantt_project_task.gantt_task_line {
   display: none !important;
}

/* ================= 主项目颜色（虽然隐藏了长条，但我们保留一下它的类逻辑配置备用） ================= */

/* 1. 已完成 (绿色) */
.project_completed .gantt_task_content { background: #67c23a !important; border-color: #5daf34 !important; }
.project_completed .gantt_task_progress { background: #5daf34 !important; opacity: 1 !important; border-radius: 4px; }

/* 2. 主项目：进行中 (底色灰，进度条橙) */
.project_progress .gantt_task_content { background: #909399 !important; border-color: #82848a !important; }
.project_progress .gantt_task_progress { background: #e6a23c !important; opacity: 1 !important; border-radius: 4px; border-top-right-radius: 0; border-bottom-right-radius: 0; }

/* 3. 未开始 (纯灰) */
.project_waiting .gantt_task_content { background: #909399 !important; border-color: #82848a !important; }

/* 4. 超期 (纯红) */
.project_overdue .gantt_task_content { background: #f56c6c !important; border-color: #e35555 !important; }
.project_overdue .gantt_task_progress { background: #f56c6c !important; opacity: 1 !important; border-radius: 4px;}

/* ================= 二级任务专属颜色配置 ================= */
.sub_task_completed .gantt_task_content { background: #67c23a !important; border: 0px solid #5daf34 !important; border-radius: 4px; }

/* 二级任务：进行中 (全涂橙色，不需要左橙右灰的分离) */
.sub_task_progress .gantt_task_content { background: #e6a23c !important; border: 0px solid #cf9236 !important; border-radius: 4px; }

/* 二级任务：未开始 */
.sub_task_waiting .gantt_task_content { background: #909399 !important; border: 0px solid #82848a !important; border-radius: 4px; }

/* 二级任务：超期 */
.sub_task_overdue .gantt_task_content { background: #f56c6c !important; border: 0px solid #e35555 !important; border-radius: 4px; }

/* 强制清除所有甘特条默认的最外层容器边框（防止透出 dhtmlx 自身的绿色或其他状态色） */
.all_gantt_sub_task.gantt_task_line {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

/* 浮窗拓展配置 */
.gantt_tooltip {
    font-size: 13px !important;
    color: #333 !important;
    z-index: 10000;
}
</style>
