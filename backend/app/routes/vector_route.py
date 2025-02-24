from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Response
from ..service import vector_service
import json

router = APIRouter()

@router.post("/define-graph")
def test(req: Request):
    try:
        print("inside route")
        return vector_service.define_graph()
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))