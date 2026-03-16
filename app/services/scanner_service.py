import camelot
import pandas as pd
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException, status
from typing import Any, Dict, List

class ScannerService:
    def __init__(self):
        pass

    async def scanner_template_one(self, body: List[Dict[str, Any]]):                        
        try:
            shipment_url = body['scanned_shipment_url']

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
        
            df["net_weight"] = (
                df["quantity"]
                    .astype(str)
                    .str.replace(r"\s+", ".", regex=True)
            )
            
            df["pieces_per_box"] = 0
            
            df["product"] = df["product"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
            df = df[df["product"].ne("")]
            
            df = df.drop(columns=["fish_name", "process_type", "sub_process_type", "grade", "quantity", "fillet_quantity"])
        
            df = df.reset_index(drop=True)

            return {"data": df.to_dict(orient="records")}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to process shipment file. Please try again or manually import."
            )