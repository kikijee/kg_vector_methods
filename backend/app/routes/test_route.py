from fastapi import APIRouter, HTTPException, Request
from ..service import kg_service
from ..utils import data_retrieval_util


router = APIRouter()

    
@router.get("/grab-files")
def test(req: Request):
    try:
        files = data_retrieval_util.fetch_files()
        return files
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

