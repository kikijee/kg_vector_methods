from app.routes import audio, auth, study_set, question, transcript

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import models

from .database import schemas
from .database.database import SessionLocal, engine
from .database import crud
from .service.auth import get_current_user
from starlette.status import HTTP_204_NO_CONTENT
from starlette.responses import Response
from .config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
client_url = settings.client_url

origins = [
    client_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# middleware to secure all routes starting with 'target_paths'
@app.middleware("http")
async def secure_path(request: Request, call_next):
    if request.method == "OPTIONS":
        print(f"OPTIONS request for {request.url.path}")

        response = Response(status_code=HTTP_204_NO_CONTENT)
        response.headers["Access-Control-Allow-Origin"] = client_url
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,PUT,PATCH,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            
        return response

    db = SessionLocal()
    try:
        target_paths = ["/api/gen/", "/api/study-set/","/api/question/","/api/transcript/"]

        token = request.cookies.get('pele-access-token')
        
        if any(request.url.path.startswith(path) for path in target_paths):
            try:
                user = await get_current_user(db, token)
                request.state.user = user
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"message": e.detail})
        
        response = await call_next(request)
    finally:
        db.close()

    return response


# include different routes here
app.include_router(auth.router, prefix='/api/auth')
app.include_router(study_set.router, prefix='/api/study-set')
app.include_router(question.router, prefix='/api/question')
app.include_router(transcript.router, prefix='/api/transcript')
app.include_router(audio.router , prefix='/api/gen')


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

