import re
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi_restful.cbv import cbv
import camelot
import pandas as pd

main_router = APIRouter()

@cbv(main_router)
class MainController:
    @main_router.get('/')
    async def root(self) -> dict[str, str]:
        return { "message": "Hello World" }
    
    @main_router.get('/ping')
    async def ping(self) -> dict[str, str]:
        return { "ping": "pong" }
    
    @main_router.post('/scanner')
    async def scanner(self, body: Dict[str, Any] = Body(...)) -> dict[str, Any]:
        shipment_url = body['scanned_shipment_url']
                
        try:
            tables = await run_in_threadpool(
                camelot.read_pdf,
                shipment_url,
                pages="all"    
            )
            
            df = pd.concat([t.df for t in tables], ignore_index=True)
            df = df.dropna(how="all")

            df.columns = df.iloc[0]
            df = df.iloc[1:].reset_index(drop=True)

            df.columns = (
                df.columns
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
            
            df = df[~df.eq("").all(axis=1)]
            
            df.columns = (df.columns.str.lower().str.replace(" ", "_"))
            
            df["product"] = (
                df["fish_name"].astype(str)
                + " "
                + df["process_type"].astype(str)
                + " "
                + df["sub_process_type"].astype(str)
                + " "
                + df["grade"].astype(str)
            )
            
            df["product"] = df["product"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
            df = df[df["product"].ne("")]
            
            df = df.drop(columns=["fish_name", "process_type", "sub_process_type", "grade"])
        
            df = df.reset_index(drop=True)

            return {"data": df.to_dict(orient="records")}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to process shipment file. Please try again or manually import."
            )
        
        