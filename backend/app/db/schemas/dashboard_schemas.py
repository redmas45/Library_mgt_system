from pydantic import BaseModel
from typing import List, Optional


class BookStat(BaseModel):
    book_id: int
    title: str
    author: Optional[str]
    times_borrowed: int
    times_searched: int


class UserStat(BaseModel):
    user_id: int
    username: str
    total_borrows: int
    active_borrows: int


class DashboardOverview(BaseModel):
    total_books: int
    total_copies: int
    total_users: int
    total_borrows: int
    active_borrows: int
    overdue_borrows: int
    books_ingested: int
    books_pending: int


class DashboardResponse(BaseModel):
    overview: DashboardOverview
    most_borrowed: List[BookStat] = []
    most_searched: List[BookStat] = []
    recent_activity: List[dict] = []
    top_users: List[UserStat] = []
