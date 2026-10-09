"""Database module for managing documents, chunks, and chat history."""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import config

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    source_type = Column(String)
    file_path = Column(String)
    chunks = relationship('Chunk', back_populates='document', cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = 'chunks'
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    text = Column(Text)
    page = Column(Integer, default=1)
    chunk_index = Column(Integer, default=0)
    chunk_metadata = Column(Text)  # Renamed from metadata to avoid reserved name collision
    document = relationship('Document', back_populates='chunks')

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    citations = Column(Text)

class Database:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or config.DATABASE_URL
        self.engine = create_engine(self.db_url, connect_args={'check_same_thread': False} if 'sqlite' in self.db_url else {})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()

    async def initialize(self):
        """Initialize database tables during app startup."""
        self._create_tables()

    def _create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        
        # Check if missing column exists and dynamically alter table if needed
        inspector = inspect(self.engine)
        if 'chunks' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('chunks')]
            if 'chunk_metadata' not in columns:
                with self.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE chunks ADD COLUMN chunk_metadata TEXT"))
                    conn.commit()

    def get_session(self):
        return self.SessionLocal()

    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def add_document(self, title: str, source_type: str, file_path: str) -> int:
        session = self.get_session()
        try:
            doc = Document(title=title, source_type=source_type, file_path=file_path)
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc.id
        finally:
            session.close()

    def add_chunks(self, document_id: int, chunks: List[Dict[str, Any]]):
        session = self.get_session()
        try:
            for chunk in chunks:
                c = Chunk(
                    document_id=document_id,
                    text=chunk.get('text', ''),
                    page=chunk.get('page', 1),
                    chunk_index=chunk.get('chunk_index', 0),
                    chunk_metadata=json.dumps(chunk.get('metadata', {}))
                )
                session.add(c)
            session.commit()
        finally:
            session.close()

    def add_chat_history(self, question: str, answer: str, citations: List[Dict[str, Any]]):
        session = self.get_session()
        try:
            chat = ChatHistory(
                question=question,
                answer=answer,
                citations=json.dumps(citations)
            )
            session.add(chat)
            session.commit()
        finally:
            session.close()

    def get_document_count(self) -> int:
        """Return the total number of documents uploaded to the database."""
        session = self.get_session()
        try:
            return session.query(Document).count()
        except Exception:
            return 0
        finally:
            session.close()

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Return a list of all documents stored in the database."""
        session = self.get_session()
        try:
            docs = session.query(Document).all()
            return [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "file_path": doc.file_path
                }
                for doc in docs
            ]
        finally:
            session.close()

    def delete_document(self, document_id: int) -> bool:
        """Delete a document and its related chunks by ID."""
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == document_id).first()
            if not doc:
                return False
            session.delete(doc)
            session.commit()
            return True
        finally:
            session.close()

    def get_chat_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent chat history records."""
        session = self.get_session()
        try:
            history = session.query(ChatHistory).order_by(ChatHistory.id.desc()).limit(limit).all()
            return [
                {
                    "id": h.id,
                    "question": h.question,
                    "answer": h.answer,
                    "citations": json.loads(h.citations) if h.citations else []
                }
                for h in history
            ]
        finally:
            session.close()

    def close(self):
        """Close database connections if necessary."""
        if hasattr(self, "engine") and self.engine:
            self.engine.dispose()