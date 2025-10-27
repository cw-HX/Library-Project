# Library Management (Django)

This is a minimal Django app implementing a simple library management system.

Features:
- User registration and login. During registration user can choose role: User or Admin. Admins are created with staff status.
- Admins can add / edit / delete books.
- Users can view catalog, borrow available books, return borrowed books, and view current borrows.
- Book availability is tracked using borrow records.

Quick start (Windows PowerShell):

1. Create a Python virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies and run migrations:

```powershell
pip install -r requirements.txt
python manage.py migrate
```

3. Create a superuser (optional) and run the server:

```powershell
python manage.py createsuperuser
python manage.py runserver
```

4. Open http://127.0.0.1:8000/ in your browser.

Notes & assumptions:
- This is a demo app. SECRET_KEY in settings is a placeholder — change it for production.
- Registration allows choosing 'Admin' role which sets is_staff=True for the user; in a real app you'd restrict admin creation.
- The project uses SQLite for Django's auth/session tables and MongoDB (via MongoEngine) for app data (books, borrow records).

MongoDB (MongoEngine) setup:
- Install MongoDB locally or use a hosted MongoDB service (Atlas).
- Install Python dependencies into your virtual environment:

```powershell
pip install -r requirements.txt
```

- Set the `MONGODB_URI` environment variable to point to your MongoDB (Atlas URI or local) before running the dev server. Example (PowerShell):

```powershell
$env:MONGODB_URI = 'mongodb+srv://<user>:<pass>@cluster0.mongodb.net/mydb'
```

- With `MONGODB_URI` set you can create demo data and run the server:

```powershell
python manage.py create_demo_data
python manage.py runserver
```

Notes:
- MongoEngine-based documents do not require Django migrations. The Django relational database (SQLite) is still used for auth and other Django models.
- If you prefer everything in PostgreSQL (production), consider switching to a managed Postgres and updating `settings.py` accordingly.

Data migration from SQLite to MongoDB
- If you already have data in `db.sqlite3` (the Django ORM `Book` and
	`BorrowRecord` tables) you can migrate that data into MongoDB with the
	included management command. It preserves the original `user_id` values
	so existing users stay linked to their borrows.

```powershell
python manage.py migrate_sqlite_to_mongo
```

This command reads `db.sqlite3` in the project root and inserts documents
into your MongoDB configured via `MONGODB_URI` (or `mongodb_uri.txt` /
local MongoDB fallback).
