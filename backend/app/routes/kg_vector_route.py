from fastapi import APIRouter, HTTPException, Request
from ..service import kg_vector_service
import logging
import traceback

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
    
@router.post("/generate-graph")
def test(req: Request):
    try:
        data = kg_vector_service.generate_graph()
        return{
            "data":data
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in /generate-graph: {error_details}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


