"""MongoEngine document models for the library app.

We keep Django's auth (users) on the existing relational DB and store
application data (books and borrow records) in MongoDB using
MongoEngine. This file provides `Book` and `BorrowRecord` documents with
fields and helper methods analogous to the previous Django ORM models.
"""
from datetime import datetime

try:
    from mongoengine import Document, StringField, IntField, DateTimeField, BooleanField, ObjectIdField
    _MONGOENGINE_AVAILABLE = True
except Exception:
    # mongoengine is not installed in the current environment. Define
    # lightweight placeholders so importing this module doesn't crash the
    # application; actual database operations will raise a clear error.
    _MONGOENGINE_AVAILABLE = False

    class _MissingDependency:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("mongoengine is not installed. Install 'mongoengine' to use MongoDB models.")

    Document = object
    StringField = IntField = DateTimeField = BooleanField = ObjectIdField = lambda *a, **k: None


class Book(Document):
    """Represents a book in the catalog stored in MongoDB.

    Fields mirror the previous Django model: title, author, genre,
    and total_copies. `id` will be an ObjectId assigned by MongoDB.
    """

    meta = {'collection': 'books'}

    title = StringField(max_length=255, required=True)
    author = StringField(max_length=255, required=True)
    genre = StringField(max_length=100)
    total_copies = IntField(default=1, min_value=0)
    # Optional legacy SQLite PK for migration bookkeeping
    legacy_id = IntField()

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def borrowed_count(self):
        """Count active borrows for this book (returned=False).

        When mongoengine isn't available this will raise a helpful error.
        """
        if not _MONGOENGINE_AVAILABLE:
            raise RuntimeError("mongoengine not available; cannot compute borrowed_count")
        return BorrowRecord.objects(book_id=self.id, returned=False).count()

    @property
    def available_copies(self):
        """Compute available copies as total minus currently borrowed."""
        return max(0, self.total_copies - self.borrowed_count)


class BorrowRecord(Document):
    """Tracks a user borrowing a specific book.

    We store `user_id` (the Django User PK) and `username` for display.
    The `book_id` references the Book's ObjectId. We also store
    `book_title` to simplify listing without additional lookups.
    """

    meta = {'collection': 'borrow_records', 'indexes': ['user_id', 'book_id']}

    # store the Django user primary key (int) and username for convenience
    user_id = IntField(required=True)
    username = StringField(max_length=150)

    # store a reference to the Book's ObjectId
    book_id = ObjectIdField(required=True)
    book_title = StringField(max_length=255)

    borrow_date = DateTimeField(default=datetime.utcnow)
    returned = BooleanField(default=False)
    return_date = DateTimeField()

    def __str__(self):
        state = 'returned' if self.returned else 'borrowed'
        return f"{self.username} - {self.book_title} ({state})"

