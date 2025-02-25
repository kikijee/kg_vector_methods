from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Response
from ..service import kg_service
import json


router = APIRouter()

    
@router.post("/generate-graph")
def test(req: Request):
    try:
        data = kg_service.generate_graph()
        return{
            "data":data
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/answer-question")
async def answer(req: Request):
    try:
        body = await req.json()
        user_input = body.get("user_input")  # Access user_input from the parsed JSON
        answer, cypher_query = kg_service.answer_question(user_input)
        return {
            "answer":answer,
            "cypher_query":cypher_query
        }
    except Exception as e:
        print(f"Error route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


