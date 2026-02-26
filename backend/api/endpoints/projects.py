from fastapi import APIRouter, HTTPException
from services.file_manager import file_manager

router = APIRouter()
@router.get("/all/gantt")
async def get_all_projects_gantt():
    data = file_manager.get_all_projects_gantt()
    return data

@router.get("/{project_id}/detail")
async def get_project_detail(project_id: str):
    data = file_manager.get_project_detail(project_id)
    if not data:
        raise HTTPException(status_code=404, detail="项目详情未找到")
    return data

@router.get("/{project_id}/gantt")
async def get_project_gantt(project_id: str):
    data = file_manager.get_project_gantt(project_id)
    if not data:
        raise HTTPException(status_code=404, detail="项目甘特图数据未找到")
    return data
