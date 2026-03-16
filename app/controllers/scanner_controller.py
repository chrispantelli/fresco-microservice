from typing import Any, Dict
from fastapi import APIRouter, Body, Depends
from fastapi_restful.cbv import cbv

from app.services.scanner_service import ScannerService

scanner_router = APIRouter()

@cbv(scanner_router)
class ScannerController:
    scanner_service: ScannerService = Depends(ScannerService)
        
    @scanner_router.post('/scanner/template_one', operation_id="scanner_template_one")
    async def scanner_template_one(self, body: Any = Body(...)):
        return await self.scanner_service.scanner_template_one(body)
    
        