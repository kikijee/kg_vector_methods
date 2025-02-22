from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Response
from ..service import kg_service


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


