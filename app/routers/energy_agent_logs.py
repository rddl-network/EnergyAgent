from typing import Optional
from pydantic import conint
from fastapi import APIRouter, HTTPException

from app.RddlInteraction.utils import table_pagination
from app.dependencies import config
from app.helpers.logs import logger, get_logs, clear_logs, LogFilter


router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def retrieve_logs(
    page: Optional[conint(gt=0)] = None,
    page_size: Optional[conint(gt=0)] = None,
    ui_filter: Optional[LogFilter] = None,
):
    try:
        logs = get_logs(log_file_path=config.log_file_path, filter=ui_filter)

        if not logs and page != 1:
            raise HTTPException(status_code=404, detail="Page not found")

        return table_pagination(page, page_size, logs)
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


@router.delete("/clear")
async def delete_logs():
    if clear_logs(config.log_file_path):
        return {"status": "success", "message": "Logs cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear logs")
