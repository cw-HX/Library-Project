"""Management command to check MongoDB connectivity and provide helpful diagnostics.

This command attempts to connect to MongoDB using the same URI as the app,
runs a ping, and prints success or detailed error information with remediation steps.
"""

from django.core.management.base import BaseCommand
from library.mongo_config import get_mongodb_uri
from pymongo import MongoClient
import urllib.parse


class Command(BaseCommand):
    help = 'Check MongoDB connection and provide diagnostics.'

    def handle(self, *args, **options):
        uri = get_mongodb_uri()
        if not uri:
            self.stdout.write(self.style.ERROR('No MONGODB_URI found. Set MONGODB_URI environment variable or add to mongodb_uri.txt.'))
            return

        self.stdout.write(f'Attempting to connect to: {uri.replace(uri.split(":")[2].split("@")[0], "*****") if "@" in uri else uri}')

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            result = client.admin.command('ping')
            self.stdout.write(self.style.SUCCESS(f'Connection successful: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Connection failed: {e}'))
            self.stdout.write('\nTroubleshooting steps:')
            self.stdout.write('1. Verify username and password in Atlas (Security > Database Access).')
            self.stdout.write('2. If password contains special characters, URL-encode it.')
            self.stdout.write('3. Ensure your IP is whitelisted (Network Access > Add IP Address).')
            self.stdout.write('4. Confirm the user has readWrite role on the target database.')
            self.stdout.write('5. Test with a simple password like "TestPass123" temporarily.')
            self.stdout.write('\nExample URI format: mongodb+srv://user:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority')