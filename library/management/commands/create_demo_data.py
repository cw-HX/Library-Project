from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from library import mongo_models


class Command(BaseCommand):
    help = 'Create demo admin user and sample books in MongoDB (for manual testing)'

    def handle(self, *args, **options):
        # create admin user if missing
        admin_username = 'admin'
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(username=admin_username, email='admin@example.com', password='admin123')
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_username} / admin123'))
        else:
            self.stdout.write('Admin user already exists')

        # create sample books in MongoDB
        samples = [
            {'title': 'The Hobbit', 'author': 'J.R.R. Tolkien', 'genre': 'Fantasy', 'total_copies': 3},
            {'title': '1984', 'author': 'George Orwell', 'genre': 'Dystopian', 'total_copies': 2},
            {'title': 'Clean Code', 'author': 'Robert C. Martin', 'genre': 'Programming', 'total_copies': 1},
        ]
        created = 0
        for s in samples:
            # avoid duplicates by title+author
            if mongo_models.Book.objects(title=s['title'], author=s['author']).count() == 0:
                mongo_models.Book(**s).save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} sample books (if any).'))
