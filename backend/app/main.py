from app.routes import kg_route, vector_route, kg_vector_route, test_route

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import Response
from .config import settings

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

# include different routes here
app.include_router(kg_route.router , prefix='/api/kg')
app.include_router(vector_route.router, prefix='/api/vector')
app.include_router(kg_vector_route.router, prefix='/api/kg-vector')
app.include_router(test_route.router, prefix='/api/test')

