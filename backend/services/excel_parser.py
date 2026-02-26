import pandas as pd
import math
import re
from datetime import datetime
from typing import Tuple, List, Dict
from models.project import ProjectDetail, ProjectGantt, TaskGantt, Milestone, TaskLevel1, TaskLevel2, ProjectStatistics, ProjectIndexItem
from services.file_manager import file_manager

EXPECTED_HEADERS = [
    "编号", "里程碑", "一级任务", "二级任务", "责任部门", 
    "工期", "开始时间", "结束时间", "状态", "备注"
]
VALID_STATUSES = ["未开始", "进行中", "已完成"]

def validate_date(date_str: str) -> bool:
    if not isinstance(date_str, str):
        return False
    date_str = date_str.strip()
    
    # 匹配 YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
            
    # 匹配 YYYY-MM-DD HH:MM:SS
    if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False
            
    return False

def parse_excel(file_path: str, original_filename: str) -> Tuple[bool, List[str], List[str], str]:
    errors = []
    warnings = []
    
    try:
        df = pd.read_excel(file_path, header=None)
    except ValueError as e:
        if "Excel file format cannot be determined" in str(e):
            try:
                # 尝试当作 HTML 格式加载 (由于我们生成的模板实际上是带有 xls 后缀的 html 文件)
                dfs = pd.read_html(file_path, header=None, encoding='utf-8')
                if not dfs:
                    raise ValueError("未找到任何表格数据")
                df = dfs[0]
            except Exception as html_err:
                errors.append(f"文件读取失败 (HTML 解析失败): {str(html_err)}")
                return False, errors, warnings, ""
        else:
            errors.append(f"文件读取失败: {str(e)}")
            return False, errors, warnings, ""
    except Exception as e:
        errors.append(f"文件读取失败: {str(e)}")
        return False, errors, warnings, ""

    if len(df) < 2:
        errors.append("文件格式错误：行数过少。第一行应为项目名称，第二行应为列头。")
        return False, errors, warnings, ""

    project_name = str(df.iloc[0, 0]).strip()
    if pd.isna(project_name) or not project_name:
        errors.append("文件格式错误：第一行第一列应为项目名称。")

    headers = df.iloc[1].fillna("").astype(str).str.strip().tolist()
    
    # 截取有效列
    if len(headers) < len(EXPECTED_HEADERS):
        errors.append("列头格式不正确，缺少必要的列。")
    else:
        headers = headers[:len(EXPECTED_HEADERS)]
        for i, h in enumerate(EXPECTED_HEADERS):
            if headers[i] != h:
                errors.append(f"列头格式不正确：第 {i+1} 列应为 '{h}'，实际为 '{headers[i]}'。")
                break

    if errors:
        return False, errors, warnings, ""

    # 从第三行读取数据
    data_df = df.iloc[2:].copy()
    data_df = data_df.iloc[:, :len(EXPECTED_HEADERS)]
    data_df.columns = EXPECTED_HEADERS
    
    # 向前填充 里程碑, 但需要按里程碑分组填充一级任务
    data_df["里程碑"] = data_df["里程碑"].ffill()
    
    # 分组填充一级任务
    data_df["一级任务"] = data_df.groupby("里程碑")["一级任务"].ffill()
    
    parsed_tasks = []
    ids = set()
    rows_count = len(data_df)
    
    for idx, row in data_df.iterrows():
        row_num = idx + 1
        
        # 1. 编号校验
        task_id = row["编号"]
        if pd.isna(task_id):
            errors.append(f"第 {row_num} 行：编号不能为空。")
        else:
            try:
                task_id_int = int(task_id)
                if task_id_int <= 0:
                    errors.append(f"第 {row_num} 行：编号必须为正整数。")
                if task_id_int in ids:
                    errors.append(f"第 {row_num} 行：编号 {task_id_int} 重复。")
                ids.add(task_id_int)
            except ValueError:
                errors.append(f"第 {row_num} 行：编号必须为整数。")

        # 2. 层级关系校验
        milestone = str(row["里程碑"]).strip() if pd.notna(row["里程碑"]) else ""
        level1 = str(row["一级任务"]).strip() if pd.notna(row["一级任务"]) else ""
        level2 = str(row["二级任务"]).strip() if pd.notna(row["二级任务"]) else ""
        
        if level2 and not level1:
            warnings.append(f"第 {row_num} 行：存在二级任务但一级任务为空。")
        if level1 and not milestone:
            errors.append(f"第 {row_num} 行：存在一级任务但里程碑为空。")

        # 3. 责任部门
        dept_raw = str(row["责任部门"]) if pd.notna(row["责任部门"]) else ""
        depts = []
        if dept_raw and str(dept_raw).lower() != "nan":
            # 支持以换行符、逗号（中英文）、分号（中英文）、空格等符号分割
            depts = [d.strip() for d in re.split(r'[\n\r,，;；\s]+', dept_raw) if d.strip()]

        # 4. 日期校验
        start_date = str(row["开始时间"]).strip() if pd.notna(row["开始时间"]) else ""
        end_date = str(row["结束时间"]).strip() if pd.notna(row["结束时间"]) else ""
        
        if start_date and not validate_date(start_date):
            errors.append(f"第 {row_num} 行：开始时间格式必须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，当前为 '{start_date}'。")
        if end_date and not validate_date(end_date):
            errors.append(f"第 {row_num} 行：结束时间格式必须为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，当前为 '{end_date}'。")

        # 5. 工期校验
        duration = row["工期"]
        if pd.notna(duration) and str(duration).strip():
            try:
                int(float(duration)) # 尝试转为float再判断是否整数不太对，需求说必须是整数，不能是小数
                if '.' in str(duration):
                    errors.append(f"第 {row_num} 行：工期必须为整数。")
            except ValueError:
                errors.append(f"第 {row_num} 行：工期必须为整数。")

        # 6. 状态校验
        status = str(row["状态"]).strip() if pd.notna(row["状态"]) else ""
        if not status or str(status).lower() == "nan":
            errors.append(f"第 {row_num} 行：状态不能为空。")
        elif status not in VALID_STATUSES:
            errors.append(f"第 {row_num} 行：状态只能为未开始、进行中、已完成。当前为 '{status}'。")

        remarks = str(row["备注"]).strip() if pd.notna(row["备注"]) else ""
        if remarks.lower() == "nan":
            remarks = ""

        # 添加到解析的数据
        if not errors:
            parsed_tasks.append({
                "id": str(task_id_int) if 'task_id_int' in locals() else "",
                "milestone": milestone,
                "level1": level1,
                "level2": level2,
                "departments": depts,
                "start": start_date,
                "end": end_date,
                "status": status,
                "remarks": remarks
            })

    # 编号完整性（连续从1开始）
    if ids and len(errors) == 0:
        if min(ids) != 1 or max(ids) != len(ids):
            errors.append("编号必须为连续不重复的正整数，从1开始。")

    if errors:
        return False, errors, warnings, ""

    # 解析成功，生成 JSON 数据
    project_id = file_manager.generate_project_id(original_filename)
    generate_json_files(project_id, project_name, original_filename, parsed_tasks, warnings)

    return True, [], warnings, project_id

def score_status(status: str) -> float:
    if status == "已完成": return 100.0
    if status == "进行中": return 50.0
    return 0.0

def generate_json_files(project_id: str, project_name: str, display_name: str, tasks: List[dict], warnings: List[str]):
    # 构建层级结构
    milestones_dict = {}
    gantt_tasks = []
    
    completed_count = 0
    in_progress_count = 0
    total_tasks = len(tasks)
    
    # 简单统计 overdue (依赖于当前日期？不，后端不实时统计overdue，交由前端，这里随便填个0)
    for t in tasks:
        # 甘特图数据
        name = t["level2"] if t["level2"] else (t["level1"] if t["level1"] else t["milestone"])
        progress = score_status(t["status"])
        
        gantt_tasks.append(TaskGantt(
            id=f"task_{t['id']}",
            name=name,
            milestone=t["milestone"],
            parent_task=t["level1"],
            start=t["start"],
            end=t["end"],
            progress=progress,
            status=t["status"],
            departments=t["departments"]
        ))
        
        if t["status"] == "已完成":
            completed_count += 1
        elif t["status"] == "进行中":
            in_progress_count += 1
            
        # 构建 Detail 结构树
        ms_name = t["milestone"]
        l1_name = t["level1"]
        
        if ms_name not in milestones_dict:
            milestones_dict[ms_name] = {"tasks_level1": {}}
            
        if l1_name:
            if l1_name not in milestones_dict[ms_name]["tasks_level1"]:
                milestones_dict[ms_name]["tasks_level1"][l1_name] = []
            milestones_dict[ms_name]["tasks_level1"][l1_name].append(t)
        else:
            # 只有里程碑的任务
            if "" not in milestones_dict[ms_name]["tasks_level1"]:
                milestones_dict[ms_name]["tasks_level1"][""] = []
            milestones_dict[ms_name]["tasks_level1"][""].append(t)
            
    # 计算百分比并整理模型
    milestones_list = []
    overall_progress_sum = 0
    
    for ms_name, ms_data in milestones_dict.items():
        l1_list = []
        ms_progress_sum = 0
        ms_count = len(ms_data["tasks_level1"])
        
        ms_start = "9999-99-99"
        ms_end = "0000-00-00"
        
        for l1_name, t_list in ms_data["tasks_level1"].items():
            l2_list = []
            l1_progress_sum = 0
            
            l1_start = "9999-99-99"
            l1_end = "0000-00-00"
            l1_status = "未开始"
            
            for t in t_list:
                p = score_status(t["status"])
                l1_progress_sum += p
                
                if t["start"] and t["start"] < l1_start: l1_start = t["start"]
                if t["end"] and t["end"] > l1_end: l1_end = t["end"]
                
                if t["level2"]:
                    l2_list.append(TaskLevel2(
                        name=t["level2"],
                        start_date=t["start"],
                        end_date=t["end"],
                        progress=p,
                        status=t["status"],
                        departments=t["departments"],
                        remarks=t["remarks"]
                    ))
                else:
                    l1_status = t["status"]

            l1_prog = l1_progress_sum / len(t_list) if t_list else 0
            ms_progress_sum += l1_prog
            
            if l1_start < ms_start: ms_start = l1_start
            if l1_end > ms_end: ms_end = l1_end

            if l1_name:
                # 代表有一个一级任务
                l1_list.append(TaskLevel1(
                    name=l1_name,
                    start_date=l1_start if l1_start != "9999-99-99" else "",
                    end_date=l1_end if l1_end != "0000-00-00" else "",
                    progress=l1_prog,
                    status="进行中" if 0 < l1_prog < 100 else ("已完成" if l1_prog == 100 else "未开始"),
                    departments=t_list[0]["departments"] if not l2_list else [], 
                    remarks="", 
                    tasks_level2=l2_list
                ))
            
        ms_prog = ms_progress_sum / ms_count if ms_count else 0
        overall_progress_sum += ms_prog
        milestones_list.append(Milestone(
            name=ms_name,
            start_date=ms_start if ms_start != "9999-99-99" else "",
            end_date=ms_end if ms_end != "0000-00-00" else "",
            progress=ms_prog,
            tasks_level1=l1_list
        ))
        
    overall_progress = overall_progress_sum / len(milestones_dict) if milestones_dict else 0
        
    stats = ProjectStatistics(
        total_tasks=total_tasks,
        completed_tasks=completed_count,
        overdue_tasks=0, # 由前端计算
        in_progress_tasks=in_progress_count,
        overall_progress=overall_progress
    )
    
    detail = ProjectDetail(
        project_id=project_id,
        project_name=project_name,
        upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        statistics=stats,
        milestones=milestones_list
    )
    
    gantt = ProjectGantt(
        project_id=project_id,
        project_name=project_name,
        tasks=gantt_tasks
    )
    
    project_start_date = "9999-99-99"
    project_end_date = "0000-00-00"
    for t in tasks:
        if t["start"] and t["start"] < project_start_date: project_start_date = t["start"]
        if t["end"] and t["end"] > project_end_date: project_end_date = t["end"]
        
    index_item = ProjectIndexItem(
        project_id=project_id,
        project_name=project_name,
        upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        display_name=display_name,
        task_count=total_tasks,
        overall_progress=overall_progress,
        warning_count=len(warnings),
        start_date=project_start_date if project_start_date != "9999-99-99" else "",
        end_date=project_end_date if project_end_date != "0000-00-00" else ""
    )
    
    file_manager.save_project_data(
        project_id,
        detail.model_dump(),
        gantt.model_dump(),
        index_item.model_dump()
    )
