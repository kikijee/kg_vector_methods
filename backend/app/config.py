import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    client_url: str = os.getenv("CLIENT_URL")

    neo4j_uri: str = os.getenv("NEO4J_URI")
    neo4j_user: str = os.getenv("NEO4J_USERNAME")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD")

    neo4j_uri_1: str = os.getenv("NEO4J_URI_1")
    neo4j_user_1: str = os.getenv("NEO4J_USERNAME_1")
    neo4j_password_1: str = os.getenv("NEO4J_PASSWORD_1")

    neo4j_uri_2: str = os.getenv("NEO4J_URI_2")
    neo4j_user_2: str = os.getenv("NEO4J_USERNAME_2")
    neo4j_password_2: str = os.getenv("NEO4J_PASSWORD_2")

    p_neo4j_uri: str = os.getenv("P_NEO4J_URI")
    p_neo4j_user: str = os.getenv("P_NEO4J_USERNAME")
    p_neo4j_password: str = os.getenv("P_NEO4J_PASSWORD")

    def __init__(self):
        if not self.openai_api_key:
            raise RuntimeError("OpenAI API key not found. Ensure it's set in the .env file.")
        elif not self.secret_key:
            raise RuntimeError("secret_key not found. Ensure it's set in the .env file.")
        elif not self.algorithm:
            raise RuntimeError("algorithm. Ensure it's set in the .env file.")
        elif not self.access_token_expire_minutes:
            raise RuntimeError("access_token_expire_minutes key not found. Ensure it's set in the .env file.")
        elif not self.client_url:
            raise RuntimeError("clinet url not found. Ensure it's set in the .env file.")

settings = Settings()

