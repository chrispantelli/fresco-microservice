from typing import Any, Dict
from fastapi import APIRouter, Body, Depends
from fastapi_restful.cbv import cbv

from app.services.report_service import ReportService

report_router = APIRouter()

@cbv(report_router)
class ReportController:
    report_service: ReportService = Depends(ReportService)
        
    @report_router.post('/reports/{report_id}', operation_id="create_release_form")
    async def create_release_form(self, report_id: str, body: Dict[str, Any] = Body(...)):
        return await self.report_service.generate(report_id, body)
        
        