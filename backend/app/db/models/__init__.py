# Models package — import all models so Alembic and Base.metadata see them
from app.db.models.user import User  # noqa: F401
from app.db.models.book import Book  # noqa: F401
from app.db.models.book_copy import BookCopy  # noqa: F401
from app.db.models.borrow_record import BorrowRecord  # noqa: F401
from app.db.models.interaction import Interaction  # noqa: F401
from app.db.models.reading_stats import ReadingStats  # noqa: F401
