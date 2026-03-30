import camelot
import pandas as pd
import tabula
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
            
    async def scanner_template_two(self, body: List[Dict[str, Any]]):
        try:
            shipment_url = body['scanned_shipment_url']

            tables = await run_in_threadpool(
                camelot.read_pdf,
                shipment_url,
                pages="all"
            )

            df = pd.concat([t.df for t in tables], ignore_index=True)
            df = df.dropna(how="all")

            df = df[~df[0].astype(str).str.contains(
                r"DESCRIPTION|TOTAL|LATIN NAME|#SAYI|^$",
                case=False,
                na=False
            )]

            df = df[df[0].astype(str).str.strip() != "0"]
            df = df.reset_index(drop=True)

            split_desc = df[0].astype(str).str.split("\n", n=1, expand=True)

            df["product"] = (
                split_desc[0].fillna("").str.strip()
                + " "
                + split_desc[1].fillna("").str.strip()
            ).str.replace(r"\s+", " ", regex=True).str.strip()

            def clean_number(col):
                return pd.to_numeric(
                    col.astype(str)
                    .str.replace(",", ".", regex=False)
                    .str.replace(r"[^\d.]", "", regex=True),
                    errors="coerce"
                )

            df["boxes"] = clean_number(df[1]).fillna(0).astype(int)
            df["net_weight"] = clean_number(df[2])
            df["total_net_weight"] = clean_number(df[3])
            df["gross_weight"] = clean_number(df[4])

            df_clean = df[[
                "product",
                "boxes",
                "net_weight",
                "total_net_weight",
                "gross_weight"
            ]].copy()

            df_clean = df_clean[df_clean["product"].ne("")]
            df_clean = df_clean[df_clean["boxes"] > 0].reset_index(drop=True)

            df_clean["row_id"] = df_clean.index

            df_clean = df_clean.loc[df_clean.index.repeat(df_clean["boxes"])].reset_index(drop=True)

            df_clean["box_number"] = range(1, len(df_clean) + 1)
            df_clean["pieces_per_box"] = 1

            df_clean = df_clean[[
                "box_number",
                "product",
                "pieces_per_box",
                "net_weight"
            ]]

            return {"data": df_clean.to_dict(orient="records")}

        except Exception as e:
            print(f"scanner_template_two failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process shipment file. Please try again or manually import."
            )
            
    async def scanner_template_three(self, body: List[Dict[str, Any]]):
        try:
            shipment_url = body["scanned_shipment_url"]

            tables = await run_in_threadpool(
                tabula.read_pdf,
                shipment_url,
                pages="all",
                multiple_tables=True
            )

            df = pd.concat(tables, ignore_index=True)

            df = df.dropna(how="all")
            df = df.dropna(axis=1, how="all")

            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True)
                .str.lower()
            )

            df = df.rename(columns={"unnamed:_0": "description"})

            COLUMN_MAPPING = {
                "caja": "box_number",
                "description": "product",
                "cantidad": "net_weight",
            }

            df = df.rename(columns=COLUMN_MAPPING)

            if "net_weight" in df.columns:
                df["net_weight"] = (
                    df["net_weight"]
                    .astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                df["net_weight"] = pd.to_numeric(df["net_weight"], errors="coerce")

            if "product" in df.columns:
                df["product"] = (
                    df["product"]
                    .astype(str)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                )

            df["pieces_per_box"] = 1

            df = df[[
                "box_number",
                "product",
                "pieces_per_box",
                "net_weight"
            ]]

            # Remove bad rows
            df = df[df["product"].notna() & (df["product"] != "")]
            df = df[df["box_number"].notna()]

            df = df.reset_index(drop=True)

            return {"data": df.to_dict(orient="records")}
        except Exception as e:
            print(f"scanner_template_three failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process shipment file. Please try again or manually import."
            )
            
    async def scanner_template_four(self, body: List[Dict[str, Any]]):
        try:
            shipment_url = "https://gamghgjxgnpbshhdseea.supabase.co/storage/v1/object/public/scanned-shipments/FRESCO%20PL_29%20MARCH%202026.pdf"

            tables = await run_in_threadpool(
                tabula.read_pdf,
                shipment_url,
                pages="all",
                multiple_tables=True
            )

            df = pd.concat(tables, ignore_index=True)
            
            df = df.where(pd.notnull(df), None)
            
            df = df.dropna(how="all")
            df = df.dropna(axis=1, how="all")

            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True)
                .str.lower()
            )

            
            df["box_number"] = df["box_no"]
            
            df["product"] = (
                df["fish_type_cut_type_skin_type"].astype(str)
                + " "
                + df["grade"].astype(str)
            )
            
            df["net_weight"] = df["weight"]
            
            df["pieces_per_box"] = df["pcs"]
            
            df = df.drop(columns=['box_no', 'fish_type_cut_type_skin_type', 'grade', 'weight', 'pcs'])

            return {"data": df.to_dict(orient="records")}
        except Exception as e:
            print(f"scanner_template_four failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process shipment file. Please try again or manually import."
            )