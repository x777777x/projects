import os
import json
import logging
import hashlib
from datetime import datetime
from filelock import FileLock
from core.config import settings

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.index_file = os.path.join(settings.DATA_DIR, "file_index.json")
        self.lock_file = os.path.join(settings.DATA_DIR, "file_index.json.lock")
        self._init_index()

    def _init_index(self):
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump({"projects": []}, f, ensure_ascii=False, indent=2)

    def generate_project_id(self, original_filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 哈希确保唯一性，短一点
        hash_str = hashlib.md5(f"{timestamp}_{original_filename}".encode()).hexdigest()[:6]
        return f"proj_{timestamp}_{hash_str}"

    def get_upload_path(self, project_id: str, original_filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = original_filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return os.path.join(settings.UPLOAD_DIR, f"{timestamp}_{project_id}_{safe_filename}")

    def save_project_data(self, project_id: str, detail_data: dict, gantt_data: dict, index_item: dict):
        # 1. 保存详情和甘特图
        detail_path = os.path.join(settings.DATA_DIR, f"{project_id}_detail.json")
        gantt_path = os.path.join(settings.DATA_DIR, f"{project_id}_gantt.json")
        
        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)
            
        with open(gantt_path, "w", encoding="utf-8") as f:
            json.dump(gantt_data, f, ensure_ascii=False, indent=2)
            
        # 2. 更新索引
        with FileLock(self.lock_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            index_data["projects"].insert(0, index_item) # 加到最前
            
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

    def get_all_projects(self):
        if not os.path.exists(self.index_file):
            return []
        with open(self.index_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            projects = data.get("projects", [])
            
            # 动态实时计算超时数量
            today_str = datetime.now().strftime("%Y-%m-%d")
            for project in projects:
                overdue_count = 0
                completed_count = 0
                in_progress_count = 0
                unstarted_count = 0
                
                detail_path = os.path.join(settings.DATA_DIR, f"{project['project_id']}_detail.json")
                if os.path.exists(detail_path):
                    with open(detail_path, "r", encoding="utf-8") as df:
                        detail_data = json.load(df)
                        milestones = detail_data.get("milestones", [])
                        for ms in milestones:
                            for l1 in ms.get("tasks_level1", []):
                                tasks_to_check = l1.get("tasks_level2", [])
                                if not tasks_to_check:
                                    # 如果没有二级任务，那么一级任务自身算一个任务
                                    tasks_to_check = [l1]
                                    
                                for task in tasks_to_check:
                                    start = task.get("start_date")
                                    end = task.get("end_date")
                                    status = task.get("status")
                                    
                                    if status == "已完成":
                                        completed_count += 1
                                    elif status == "进行中":
                                        in_progress_count += 1
                                    elif status == "未开始":
                                        unstarted_count += 1
                                        
                                    if start and end:
                                        if start <= today_str <= end and status == "未开始":
                                            overdue_count += 1
                                        elif today_str > end and status != "已完成":
                                            overdue_count += 1
                                            
                project["overdue_count"] = overdue_count
                project["completed_tasks"] = completed_count
                project["in_progress_tasks"] = in_progress_count
                project["unstarted_tasks"] = unstarted_count
                
            return projects

    def delete_project(self, project_id: str) -> bool:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with FileLock(self.lock_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            # 找到项目
            project = next((p for p in index_data["projects"] if p["project_id"] == project_id), None)
            if not project:
                return False
                
            # 从列表移除
            index_data["projects"] = [p for p in index_data["projects"] if p["project_id"] != project_id]
            
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        # 移动文件到 deleted (如果有错也不抛出，尽力而为)
        try:
            detail_path = os.path.join(settings.DATA_DIR, f"{project_id}_detail.json")
            gantt_path = os.path.join(settings.DATA_DIR, f"{project_id}_gantt.json")
            
            if os.path.exists(detail_path):
                os.rename(detail_path, os.path.join(settings.DELETED_DIR, f"{project_id}_detail_deleted_{timestamp}.json"))
            if os.path.exists(gantt_path):
                os.rename(gantt_path, os.path.join(settings.DELETED_DIR, f"{project_id}_gantt_deleted_{timestamp}.json"))
                
            # 找到原始上传的文件（前缀可能不一致，只按包含 project_id 查找）
            for file in os.listdir(settings.UPLOAD_DIR):
                if project_id in file:
                    source_file = os.path.join(settings.UPLOAD_DIR, file)
                    os.rename(source_file, os.path.join(settings.DELETED_DIR, f"deleted_{timestamp}_{file}"))
        except Exception as e:
            logger.error(f"Error moving files for deleted project {project_id}: {e}")
            
        return True

    def get_project_detail(self, project_id: str):
        path = os.path.join(settings.DATA_DIR, f"{project_id}_detail.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_project_gantt(self, project_id: str):
        path = os.path.join(settings.DATA_DIR, f"{project_id}_gantt.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_all_projects_gantt(self):
        projects = self.get_all_projects()
        result = []
        for p in projects:
            # 拿到汇总信息
            proj_data = {
                "id": p["project_id"],
                "text": p["project_name"],
                "start_date": p["start_date"],
                "end_date": p["end_date"],
                "overall_progress": p["overall_progress"],
                "overdue_count": p["overdue_count"],
                "task_count": p["task_count"],
                "type": "project"
            }
            
            # 再拿到每项里的二级任务组合子集
            detail = self.get_project_detail(p["project_id"])
            children = []
            if detail:
                milestones = detail.get("milestones", [])
                for ms in milestones:
                    for l1 in ms.get("tasks_level1", []):
                        tasks = l1.get("tasks_level2", [])
                        if not tasks:
                            tasks = [l1]
                        
                        for t in tasks:
                            # 过滤没有起止时间的脏数据
                            if not t.get("start_date") or not t.get("end_date"):
                                continue
                            
                            # ID 防重必须加上项目 ID
                            # 对于从 Detail 里取的任务由于原来没有存原生 ID，可以用 hash 或拼接字段。
                            # 稳妥起见我们去拿 _gantt.json 文件中已经整理好的底层任务
                            pass
                            
            # 建立一个备注字典，以便从 detail.json 补齐 _gantt.json 中丢失的 remark
            remark_map = {}
            if detail:
                for ms in detail.get("milestones", []):
                    for l1 in ms.get("tasks_level1", []):
                        tasks = l1.get("tasks_level2", [])
                        if not tasks:
                            tasks = [l1]
                        for t in tasks:
                            if t.get("task_name"):
                                remark_map[t["task_name"]] = t.get("remark", "")

            # 或者干脆取 _gantt.json 来找最底层任务
            gantt = self.get_project_gantt(p["project_id"])
            if gantt and "tasks" in gantt:
                for idx, t in enumerate(gantt["tasks"]):
                    # 由于 gantt.json 中的任务没有携带备注，我们可以借用 `detail.json` 的。
                    t_name = t.get("name", "")
                    t_remark = remark_map.get(t_name, "")
                    
                    children.append({
                        "id": f"{p['project_id']}_{t['id']}_{idx}",
                        "text": t_name,
                        "start_date": t["start"],
                        "end_date": t["end"],
                        "status": t["status"],
                        "remark": t_remark,
                        "parent": p["project_id"],
                        "progress": t["progress"], # progress 实际上没有用在动态图计算了
                        "type": "task",
                        "milestone": t.get("milestone", ""),
                        "level1": t.get("parent_task", "")
                    })
            
            proj_data["children"] = children
            result.append(proj_data)
            
        return result

file_manager = FileManager()
