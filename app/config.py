import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Make sure these fields are present in your Config class:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    
    # Keep your other existing configurations (database url, chunk size, etc.)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rag.db")
    APP_NAME: str = os.getenv("APP_NAME", "CCA AI Assistant")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 512))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 20))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", 3))

    # Vector Store
    VECTOR_DIMENSION = 1536

    # File Upload
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md", ".docx", ".doc"]

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "your-gemini-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )
        return True

    @classmethod
    def get_allowed_extensions(cls) -> List[str]:
        """Get list of allowed file extensions."""
        return cls.ALLOWED_EXTENSIONS

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if a file extension is allowed."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS


# Global instance imported by main.py
config = Config()