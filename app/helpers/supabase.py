import os
from supabase import create_client, Client

def superset_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY enviroment variables")
    
    return create_client(url, key)