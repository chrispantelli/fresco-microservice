import os
from fastapi import Depends, FastAPI, HTTPException
from supabase import Client

# Controllers
from app.controllers.main_controller import main_router
from app.controllers.report_controller import report_router

from app.services.generate_collection_form import generate_collection_form_pdf

from .services.generate_release_form import generate_release_form_pdf
from .helpers.supabase import superset_client

app = FastAPI()

def start_application() -> FastAPI:
    application = FastAPI(
        title="Fresco Microservice",
        debug=False
    )
    
    application.include_router(main_router)
    application.include_router(report_router)
    
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
        

# @app.get("/")
# def read_root():
#     return {"message": "Welcome!"}

# @app.get("/ping")
# def health():
#     return {"pong"}

# # @app.post("/reports/release-form/{report_id}")
# # async def generate_release_form(report_id: str, request: Request, supabase: Client = Depends(superset_client)):
# #     background_task = supabase.table('tblbackgroundtasks').insert({ 'id': str(ULID()), 'status': 'generating', 'type': 'release-form', 'type_id': report_id, 'message': None }).execute()
# #     bg_task_id = background_task.data[0]['id']
    
# #     data = await request.json()
    
# #     try:
    #     response = supabase.table("tblreports").select("*").eq("id", report_id).execute()
    #     if not response.data:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Report not found' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=404, detail="Report not found")

    #     storage_company = data.get("storage_company")
    #     report_body = response.data[0]["body"]

    #     pdf_bytes = generate_release_form_pdf(report_body, storage_company)

    #     upload_response = supabase.storage.from_("generated-reports").upload(
    #         path=f"release-forms/{report_id}.pdf",
    #         file=pdf_bytes,
    #         file_options={"content-type": "application/pdf", "upsert": "true"}
    #     )

    #     if not upload_response:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Failed to upload PDF' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=500, detail="Failed to upload PDF")

    #     public_url = (
    #         f"{os.environ.get('SUPABASE_URL')}/storage/v1/object/public/"
    #         f"{upload_response.full_path}"
    #     )

    #     update_response = supabase.table("tblreports").update({
    #         "generated_pdf": public_url
    #     }).eq("id", report_id).execute()

    #     if not update_response.data:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Failed to update report record' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=500, detail="Failed to update report record")

    #     supabase.table('tblbackgroundtasks').update({ 'status': 'success', 'message': 'Report Generated' }).eq('id', bg_task_id).execute()
    #     return {"status": "success", "url": public_url}

    # except HTTPException as e:
    #     supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': e }).eq('id', bg_task_id).execute()
    #     raise e

    # except Exception as e:
    #     supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': e }).eq('id', bg_task_id).execute()
    #     raise HTTPException(status_code=500, detail=str(e))
    
# # @app.post("/reports/collection-form/{report_id}")
# # async def generate_collection_form(report_id: str, request: Request, supabase: Client = Depends(superset_client)):
    # background_task = supabase.table('tblbackgroundtasks').insert({ 'id': str(ULID()), 'status': 'generating', 'type': 'collection-form', 'type_id': report_id, 'message': None }).execute()
    # bg_task_id = background_task.data[0]['id']
    
    # data = await request.json()
    
    # try:
    #     response = supabase.table("tblreports").select("*").eq("id", report_id).execute()
    #     if not response.data:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Report not found' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=404, detail="Report not found")

    #     transport_company = data.get("transport_company")
    #     report_body = response.data[0]["body"]

    #     pdf_bytes = generate_collection_form_pdf(report_body, transport_company)

    #     upload_response = supabase.storage.from_("generated-reports").upload(
    #         path=f"release-forms/{report_id}.pdf",
    #         file=pdf_bytes,
    #         file_options={"content-type": "application/pdf", "upsert": "true"}
    #     )

    #     if not upload_response:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Failed to upload PDF' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=500, detail="Failed to upload PDF")

    #     public_url = (
    #         f"{os.environ.get('SUPABASE_URL')}/storage/v1/object/public/"
    #         f"{upload_response.full_path}"
    #     )

    #     update_response = supabase.table("tblreports").update({
    #         "generated_pdf": public_url
    #     }).eq("id", report_id).execute()

    #     if not update_response.data:
    #         supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': 'Failed to update report record' }).eq('id', bg_task_id).execute()
    #         raise HTTPException(status_code=500, detail="Failed to update report record")

    #     supabase.table('tblbackgroundtasks').update({ 'status': 'success', 'message': 'Report Generated' }).eq('id', bg_task_id).execute()
    #     return {"status": "success", "url": public_url}

    # except HTTPException as e:
    #     supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': e }).eq('id', bg_task_id).execute()
    #     raise e

    # except Exception as e:
    #     supabase.table('tblbackgroundtasks').update({ 'status': 'failed', 'message': e }).eq('id', bg_task_id).execute()
    #     raise HTTPException(status_code=500, detail=str(e))