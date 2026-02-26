from fastapi import APIRouter
from api.endpoints import files, projects

api_router = APIRouter()
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
