from django.contrib.auth.models import User
from main.models import Post, Comment
from .e621_api import E621APIClient
from django.db import transaction
from typing import List
from tqdm import tqdm

class PostImporter:
    def __init__(self, api_client: E621APIClient):
        self.api_client = api_client

    @transaction.atomic
    def import_for_tags(self, tags: List[str]):
        self.api_client.limit
        posts_data = self.api_client.fetch_posts(tags)
        total_posts = len(posts_data)
        print(f"Найдено постов: {total_posts}")

        for data in tqdm(posts_data, desc="Импорт постов", ncols=100, position=0, leave=True):
            file_url = data.get("file", {}).get("url")
            file_ext = data.get("file", {}).get("ext", "").lower()
            if not file_url or file_ext not in ("jpg", "jpeg", "png", "gif"):
                continue

            author_name = data.get("tags", {}).get("artist", [])
            author = author_name[0] if author_name else "unknown"
            django_username = f"e621User({author})"
            user, created = User.objects.get_or_create(username=django_username)
            if created:
                user.set_unusable_password()
                user.save()

            raw_description = data.get("description", "")
            if raw_description:
                title = raw_description.splitlines()[0].strip()
                if not title:
                    title = f"e621 post by {author}"
            else:
                title = f"e621 post by {author}"

            tags_list = data.get("tags", {}).get("general", [])
            score = data.get("score", 0)
            likes = 0
            dislikes = 0
            if score != 0:
                likes = int(score["up"])
                dislikes = -int(score["down"])

            Post.objects.update_or_create(
                url=file_url,
                defaults={
                    "user": user,
                    "title": title[:200],
                    "tags": tags_list,
                    "likes": likes,
                    "dislikes": dislikes,
                    "views": data.get("fav_count", 0),
                    "posted": data.get("created_at", {}),
                    "comments_count": 0,
                }
            )

        print("\nИмпорт завершён успешно!")