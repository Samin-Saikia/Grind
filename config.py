import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "grind-local-secret-2024")
    SQLALCHEMY_DATABASE_URI = "sqlite:///grind.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

config = Config()
