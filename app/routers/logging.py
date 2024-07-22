from typing import List

from fastapi import APIRouter, HTTPException

from app.dependencies import config
from app.helpers.logs import logger, get_logs, clear_logs, LogEntry, LogFilter

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[LogEntry])  # type: ignore
async def retrieve_logs(limit: int = 100, filter: LogFilter = None):
    logs = get_logs(config.log_file_path, limit, filter)
    if not logs:
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")
    return logs


@router.post("/add")
async def add_log(level: str, message: str):
    try:
        if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")

        log_function = getattr(logger, level.lower())
        log_function(message)
        return {"status": "success", "message": "Log added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add log: {str(e)}")
    return {"status": "success", "message": "Log added successfully"}


@router.delete("/clear")
async def delete_logs():
    if clear_logs(config.log_file_path):
        return {"status": "success", "message": "Logs cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear logs")
