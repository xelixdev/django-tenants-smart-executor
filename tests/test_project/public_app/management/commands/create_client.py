from django.core.management.base import BaseCommand

from tests.test_project.public_app.models import Client


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema_name", type=str)

    def handle(self, *args, **options):
        Client.objects.create(schema_name=options["schema_name"], name=options["schema_name"])
