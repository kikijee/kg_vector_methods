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

@router.post("/perform-search")
async def answer(req: Request):
    try:
        body = await req.json()
        user_input = body.get("user_input")  # Access user_input from the parsed JSON
        return vector_service.perform_search(user_input, 5)
    except Exception as e:
        print(f"Error route: {e}")
        raise HTTPException(status_code=500, detail=str(e))