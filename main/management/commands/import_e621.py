from django.core.management.base import BaseCommand
from services.e621.import_posts import PostImporter, E621APIClient
from django.conf import settings

class Command(BaseCommand):
    help = "Импортирует посты с e621 по тегам пользователя"

    def add_arguments(self, parser):
        parser.add_argument(
            'tags',
            nargs='+',  # один или более тегов
            type=str,
            help='Список тегов для поиска постов'
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Максимальное количество подходящих постов по предоставленным тегам'
        )

    def handle(self, *args, **options):
        tags = options['tags']  # Список тегов из командной строки
        limit = options['limit']  # Лимит выгрузки постов (по умолчанию 10)
        client = E621APIClient(settings.E621_API_USER, settings.E621_API_KEY, limit)
        importer = PostImporter(client)
        importer.import_for_tags(tags)
        self.stdout.write(self.style.SUCCESS("Посты успешно импортированы"))
