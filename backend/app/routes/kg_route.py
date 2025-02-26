from fastapi import APIRouter, HTTPException, Request
from ..service import kg_service
import logging
import traceback

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@router.post("/generate-graph")
def test(req: Request):
    try:
        data = kg_service.generate_graph()
        return{
            "data":data
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in api/kg/generate-graph: {error_details}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
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
        error_details = traceback.format_exc()
        logger.error(f"Error in /api/kg/answer-question: {error_details}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


