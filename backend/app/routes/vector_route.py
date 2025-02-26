from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Response
from ..service import vector_service
import json
import traceback
import logging

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@router.post("/generate-graph")
def test(req: Request):
    try:
        print("inside route")
        return vector_service.define_graph()
    
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in api/vector/generate-graph: {error_details}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/answer-question")
async def answer(req: Request):
    try:
        body = await req.json()
        user_input = body.get("user_input")  # Access user_input from the parsed JSON
        return vector_service.perform_search(user_input, 5)
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in api/vector/answer-question: {error_details}")
        raise HTTPException(status_code=500, detail="Internal Server Error")