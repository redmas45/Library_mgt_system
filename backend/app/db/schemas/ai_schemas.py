from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    book_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[dict] = []
    tokens_used: Optional[int] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)
    book_id: Optional[int] = None


class SearchResult(BaseModel):
    book_id: int
    book_title: str
    chunk_text: str
    relevance_score: float
    page_number: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    book_id: int = Field(..., description="ID of the book to query")


class QASource(BaseModel):
    chunk_text: str
    page_number: Optional[int] = None
    relevance_score: float


class QAResponse(BaseModel):
    question: str
    answer: str
    sources: List[QASource]
    book_title: str
    tokens_used: Optional[int] = None


class SummaryRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book to summarize")
    force_regenerate: bool = Field(False, description="Force regeneration even if cached")


class SummaryResponse(BaseModel):
    book_id: int
    book_title: str
    summary: str
    key_ideas: List[str] = []
    is_cached: bool = False
    tokens_used: Optional[int] = None
