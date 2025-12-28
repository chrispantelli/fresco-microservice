from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends
from fastapi_restful.cbv import cbv
from pydantic import BaseModel

from app.services.shipment_service import ShipmentService

shipment_router = APIRouter()

class GenerateAndSendCustomerAllocation(BaseModel):
    pass

@cbv(shipment_router)
class ShipmentController:
    shipment_service: ShipmentService = Depends(ShipmentService)
        
    @shipment_router.post('/shipments/{shipment_id}/customer-allocation', operation_id="generate_customer_allocation")
    async def generate_customer_allocation(self, shipment_id: str, body: Any = Body(...)):
        return await self.shipment_service.generate_customer_allocation(shipment_id, body)
        
        