from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
import os
import shutil
import urllib.parse
from typing import List
from models.project import FileIndex
from services.excel_parser import parse_excel
from services.file_manager import file_manager
from core.config import settings

router = APIRouter()

class PasswordVerifyRequest(BaseModel):
    password: str

@router.post("/verify-pwd")
async def verify_password(req: PasswordVerifyRequest):
    if req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误")
    return {"message": "校验通过"}

def verify_admin(x_admin_password: str = Header(None)):
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="密码错误或未提供")
    return True

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), _ = Depends(verify_admin)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只允许上传 .xlsx 或 .xls 格式的文件")
    
    # 检查文件名是否重复
    projects = file_manager.get_all_projects()
    if any(p.get("display_name") == file.filename for p in projects):
        raise HTTPException(status_code=400, detail=f"文件名 '{file.filename}' 已存在，不能重复上传")
    
    # 临时保存文件
    temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 解析文件
        success, errors, warnings, project_id = parse_excel(temp_path, file.filename)
        
        if not success:
            os.remove(temp_path)
            return JSONResponse(status_code=400, content={"message": "文件解析失败", "errors": errors, "warnings": warnings})
        
        # 解析成功，移动到最终位置
        final_path = file_manager.get_upload_path(project_id, file.filename)
        os.rename(temp_path, final_path)
        
        return {"message": "上传成功", "project_id": project_id, "warnings": warnings}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")

@router.get("", response_model=List[dict])
async def get_files():
    return file_manager.get_all_projects()

@router.delete("/{project_id}")
async def delete_file(project_id: str, _ = Depends(verify_admin)):
    success = file_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目未找到")
    return {"message": "删除成功"}

@router.get("/download/{project_id}")
async def download_file(project_id: str):
    projects = file_manager.get_all_projects()
    proj = next((p for p in projects if p.get("project_id") == project_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail="项目数据未找到")
        
    for file in os.listdir(settings.UPLOAD_DIR):
        if project_id in file:
            file_path = os.path.join(settings.UPLOAD_DIR, file)
            display_name = proj.get("display_name", file)
            encoded_name = urllib.parse.quote(display_name)
            response = FileResponse(file_path, filename=display_name)
            response.headers["Content-Disposition"] = f"attachment; filename*=utf-8''{encoded_name}"
            return response
            
    raise HTTPException(status_code=404, detail="原始Excel文件未找到或已被清理")
