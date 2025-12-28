from fastapi import FastAPI

# Controllers
from app.controllers.main_controller import main_router
from app.controllers.report_controller import report_router
from app.controllers.shipment_controller import shipment_router

app = FastAPI()

def start_application() -> FastAPI:
    application = FastAPI(
        title="Fresco Microservice",
        debug=False
    )
    
    application.include_router(main_router)
    application.include_router(report_router)
    application.include_router(shipment_router)
    
    return application

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:start_application",
        factory=True,
        host="0.0.0.0",
        port=int("8000"),
        log_level="debug",
        access_log=True,
        reload=False
    )