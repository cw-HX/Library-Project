from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    """Archived Django ORM model for Book.

    This file is an archive of the original Django models. The project has
    migrated application data to MongoDB documents; this module is kept for
    reference and to enable data export from the SQLite file when needed.
    """

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BorrowRecord(models.Model):
    """Archived Django ORM model for BorrowRecord."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(auto_now_add=True)
    returned = models.BooleanField(default=False)
    return_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'book', 'returned')

    def __str__(self):
        state = 'returned' if self.returned else 'borrowed'
        return f"{self.user.username} - {self.book.title} ({state})"
