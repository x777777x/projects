# 项目进度管理与展示系统

本项目是一个基于 FastAPI (后端) 和 Vue 3 (前端) 构建的**项目进度管理与展示系统**。系统旨在通过结构化的数据和可视化的图表，实现对复杂项目进度的高效管理。

## 一、 业务功能

系统主要提供以下核心功能：

1. **Excel 文件上传与严格校验**：支持用户上传包含项目进度和任务结构的 Excel 数据文件，后端会进行严格的数据格式和逻辑校验。
2. **JSON 数据拆分与高效加载**：对于大规模数据，系统能够将解析后的大文件自动拆分并存储为多个 JSON，从而实现前端获取庞大项目进度数据时的高效、快速加载。
3. **文件管理**：提供上传数据文件的统一管理能力（上传、读取、删除）。
4. **多维度数据可视化展示**：
   * **层级结构视图**：将项目中的任务以树状层级图表（Echarts等）的形式进行直观展示，理清父子级任务依赖。
   * **甘特图 (Gantt Chart)**：集成 `dhtmlx-gantt`，图形化展示每个任务的开始时间、结束时间以及任务进度，方便全局掌控工程耗时与节点安排。

## 二、 项目结构

该项目采用了标准的前后端分离架构，具体分为 `backend` 和 `frontend` 两个主要的目录结构：

```text
projects
├── backend                 # 后端工程 (Python / FastAPI)
│   ├── api                 # API 路由控制器层，负责接口定义
│   ├── core                # 核心配置 (如全局异常处理、CORS设置、环境变量等)
│   ├── data                # 数据存储与访问层，负责持久化或缓存操作
│   ├── models              # Pydantic 数据模型定义，用于请求与响应的数据校验
│   ├── services            # 核心业务逻辑层 (如 Excel 解析、数据拆分等核心业务)
│   ├── uploads             # 本地数据存储目录 (存放上传的 Excel 文件及拆分后的 JSON等)
│   ├── utils               # 通用工具函数
│   ├── main.py             # FastAPI 服务启动入口点
│   └── requirements.txt    # Python 扩展包依赖清单
│
└── frontend                # 前端工程 (Vue 3 / Vite)
    ├── public              # 公共静态资源
    ├── src                 # 核心代码目录
    │   ├── components      # 可复用的 Vue 业务/基础组件
    │   ├── views           # 页面级视图组件 (如工作台、项目日历、设置页面)
    │   ├── store           # Pinia 状态管理数据中心
    │   ├── utils           # 前端工具类与请求封装 (如 axios 配置)
    │   └── main.js/ts      # 前端应用挂载与启动入口
    ├── index.html          # 前端应用挂载页面底座
    ├── package.json        # 前端依赖与脚手架命令 (Element-Plus, echarts, dhtmlx-gantt 等)
    └── vite.config.js      # Vite 模块打包器构建配置
```

## 三、 项目配置与使用方法

### 1. 后端服务 (FastAPI) 启动配置

**环境要求**：Python 3.9+ 

1. **进入后端目录**：
   ```bash
   cd backend
   ```
2. **创建并激活虚拟环境 (推荐)**：
   ```bash
   python -m venv venv
   # Windows 系统激活
   .\venv\Scripts\activate
   # macOS/Linux 系统激活
   source venv/bin/activate
   ```
3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
4. **启动服务**：
   ```bash
   # 使用 uvicorn 启动，开启热更新
   uvicorn main:app --reload
   ```
   *服务默认运行在 `http://127.0.0.1:8000`。您可以访问 `http://127.0.0.1:8000/docs` 查看自动生成的 Swagger 接口文档।*

### 2. 前端服务 (Vue 3) 启动配置

**环境要求**：Node.js v18+

1. **进入前端目录**：
   ```bash
   cd frontend
   ```
2. **安装依赖包**：
   ```bash
   npm install
   ```
3. **启动开发服务器**：
   ```bash
   npm run dev
   ```
   *启动后控制台会输出本地访问地址（例如 `http://localhost:5173`），浏览器中打开该地址即可访问前端界面。*

### 3. VS Code 调试支持

项目根目录的 `.vscode/launch.json` 已配置了便捷的一键启动调试，您可以直接在 VS Code 左侧的“运行和调试”面板中，选择相应的启动项（例如启动前端、启动后端或者同时启动）。
