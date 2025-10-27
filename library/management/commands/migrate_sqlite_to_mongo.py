"""Management command to migrate Book and BorrowRecord data from SQLite to MongoDB.

Usage:
  python manage.py migrate_sqlite_to_mongo

It reads from the `db.sqlite3` file in the project root and inserts
documents into MongoDB using `library.mongo_models`. It preserves the
original `user_id` from Django's auth_user table and maps book IDs.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from library import mongo_models
from library.mongo_config import get_mongodb_uri

try:
    from mongoengine import connect
except Exception:
    connect = None


class Command(BaseCommand):
    help = 'Migrate library Book and BorrowRecord rows from db.sqlite3 into MongoDB'

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parent.parent.parent.parent
        sqlite_path = base / 'db.sqlite3'
        if not sqlite_path.exists():
            self.stderr.write('db.sqlite3 not found in project root')
            return

        # Ensure MongoEngine connected
        if connect is None:
            self.stderr.write('mongoengine is not installed. Install mongoengine to run this command.')
            return

        uri = get_mongodb_uri()
        if uri:
            connect(host=uri)
            self.stdout.write(f'Connected to MongoDB via URI')
        else:
            connect('library', host='mongodb://localhost:27017/library')
            self.stdout.write('Connected to local MongoDB (mongodb://localhost:27017/library)')

        conn = sqlite3.connect(str(sqlite_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Migrate books
        cur.execute('SELECT id, title, author, genre, total_copies FROM library_book')
        rows = cur.fetchall()
        book_map = {}  # sqlite_id -> mongo_id
        created = 0
        for r in rows:
            # avoid duplicates by legacy_id
            existing = mongo_models.Book.objects(legacy_id=r['id']).first()
            if existing:
                book_map[r['id']] = existing.id
                continue
            b = mongo_models.Book(title=r['title'], author=r['author'], genre=r['genre'] or '', total_copies=int(r['total_copies']) if r['total_copies'] is not None else 1, legacy_id=int(r['id']))
            b.save()
            book_map[r['id']] = b.id
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} books into MongoDB'))

        # Migrate borrow records
        # We need username from auth_user table
        cur.execute('SELECT id, username FROM auth_user')
        users = {row['id']: row['username'] for row in cur.fetchall()}

        cur.execute('SELECT id, user_id, book_id, borrow_date, returned, return_date FROM library_borrowrecord')
        rows = cur.fetchall()
        created = 0
        for r in rows:
            sqlite_book_id = r['book_id']
            mongo_book_id = book_map.get(sqlite_book_id)
            if not mongo_book_id:
                self.stderr.write(f'Skipping borrow record {r["id"]}: book id {sqlite_book_id} not migrated')
                continue
            username = users.get(r['user_id'], 'unknown')
            br = mongo_models.BorrowRecord(
                user_id=int(r['user_id']),
                username=username,
                book_id=mongo_book_id,
                book_title=str(r['book_id']),
                borrow_date=datetime.fromisoformat(r['borrow_date']) if r['borrow_date'] else None,
                returned=bool(r['returned']),
            )
            if r['return_date']:
                try:
                    br.return_date = datetime.fromisoformat(r['return_date'])
                except Exception:
                    br.return_date = None
            br.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} borrow records into MongoDB'))

        conn.close()
