from pydantic import BaseModel, Field
from typing import List, Optional

class TaskGantt(BaseModel):
    id: str
    name: str
    milestone: str
    parent_task: str
    start: str
    end: str
    progress: float
    status: str
    departments: List[str]

class TaskLevel2(BaseModel):
    name: str
    start_date: str
    end_date: str
    progress: float
    status: str
    departments: List[str]
    remarks: str

class TaskLevel1(BaseModel):
    name: str
    start_date: str
    end_date: str
    progress: float
    status: str
    departments: List[str]
    remarks: str
    tasks_level2: List[TaskLevel2] = []

class Milestone(BaseModel):
    name: str
    start_date: str
    end_date: str
    progress: float
    tasks_level1: List[TaskLevel1] = []

class ProjectStatistics(BaseModel):
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    in_progress_tasks: int
    overall_progress: float

class ProjectDetail(BaseModel):
    project_id: str
    project_name: str
    upload_time: str
    statistics: ProjectStatistics
    milestones: List[Milestone] = []

class ProjectGantt(BaseModel):
    project_id: str
    project_name: str
    tasks: List[TaskGantt] = []

class ProjectIndexItem(BaseModel):
    project_id: str
    project_name: str
    upload_time: str
    display_name: str
    task_count: int
    overall_progress: float
    warning_count: int
    start_date: str = ""
    end_date: str = ""

class FileIndex(BaseModel):
    projects: List[ProjectIndexItem] = []
