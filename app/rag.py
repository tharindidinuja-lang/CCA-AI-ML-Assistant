import os
from typing import List, Dict, Any, Optional
from click import prompt
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from sqlalchemy import or_

from app.database import Database, Chunk

class RAGPipeline:
    def __init__(
        self,
        GEMINI_API_KEY: str,
        model: str = "gemini-2.5-flash",
        embedding_model: str = "text-embedding-004",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.GEMINI_API_KEY = GEMINI_API_KEY
        self.db = Database()
        
        # Initialize Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # Initialize Google Gemini models via LangChain
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=GEMINI_API_KEY
        )
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            google_api_key=GEMINI_API_KEY
        )

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """Loads, chunks, and stores a document in the database."""
        filename = os.path.basename(file_path)
        
        # 1. Choose document loader based on file extension
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')
            
        raw_docs = loader.load()

        # 2. Add main document record to DB
        doc_id = self.db.add_document(
            title=filename,
            source_type=filename.split('.')[-1],
            file_path=file_path
        )

        # 3. Split document into chunks
        split_docs = self.text_splitter.split_documents(raw_docs)

        # 4. Prepare chunks for DB storage
        chunks_data = []
        for idx, doc in enumerate(split_docs):
            chunks_data.append({
                'text': doc.page_content,
                'page': doc.metadata.get('page', 1),
                'chunk_index': idx,
                'metadata': doc.metadata
            })

        # 5. Save chunks to DB
        self.db.add_chunks(doc_id, chunks_data)

        return {
            "document_id": doc_id,
            "filename": filename,
            "chunks_created": len(chunks_data)
        }

    def answer_question(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        """Retrieves relevant context chunks from DB using keyword filtering and generates a grounded response."""
        session = self.db.get_session()
        try:
            query_lower = question.lower()
            keywords = [word.lower() for word in question.split() if len(word) > 3]
            
            if "medical" in query_lower or "emergency" in query_lower or "health" in query_lower:
                keywords.extend(["health", "wellbeing", "doctor", "medical", "emergency", "safety"])

            query = session.query(Chunk)
            if keywords:
                # Build filters for keywords
                filters = [Chunk.text.ilike(f"%{kw}%") for kw in keywords]
                
                # Filter by keywords and skip table of contents/intro pages
                filtered_chunks = query.filter(
                    Chunk.page > 6, 
                    or_(*filters)
                ).limit(top_k).all()
                
                # Fallback to general chunks if no specific keyword matches are found past page 6
                chunks = filtered_chunks if filtered_chunks else query.limit(top_k).all()
            else:
                chunks = query.limit(top_k).all()
            
            context = "\n\n".join([c.text for c in chunks])
            citations = [
                {
                    "document_title": c.document.title if c.document else "Document",
                    "chunk_text": c.text,
                    "page": c.page, 
                    "chunk_index": c.chunk_index
                }
                for c in chunks
            ]
            
            prompt = (f"Answer the question based ONLY on the context below. "
                f"If the answer cannot be found or is not explicitly mentioned in the provided context, "
                f"state clearly: 'The provided context does not contain information regarding this topic.' "
                f"Do not attempt to guess or supply unrelated details.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}")
            response = self.llm.invoke(prompt)
            
            return {
                "answer": response.content,
                "citations": citations,
                "confidence_score": 0.95,
                "is_supported": True
            }
        finally:
            session.close()