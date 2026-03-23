import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///grind_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
    GROQ_MODEL = "llama3-70b-8192"

    # Fix for Supabase / Heroku postgres:// vs postgresql://
    @staticmethod
    def fix_db_url(url):
        if url and url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

config = Config()
config.SQLALCHEMY_DATABASE_URI = Config.fix_db_url(config.SQLALCHEMY_DATABASE_URI)
