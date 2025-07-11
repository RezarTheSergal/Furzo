import requests
from math import ceil
from typing import List, Dict
from tqdm import tqdm

class E621APIClient:
    BASE_URL = "https://e621.net/posts.json"
    # COMMENTS_URL = "https://e621.net/comments.json"

    def __init__(self, api_user: str, api_key: str, limit: int):
        self.api_user = api_user
        self.api_key = api_key
        self.limit = limit

    def fetch_posts(self, tags: List[str], outer_position=0) -> List[Dict]:
        tags.append("-comic")
        tags.append("-vore")
        
        all_posts = []
        pages = ceil(self.limit / 320)

        for page in tqdm(range(1, pages + 1), desc="Загрузка страниц", position=outer_position + 1, leave=False):
            # Определяем, сколько постов запрашивать на этой странице
            if page < pages:
                local_limit = 320
            else:
                local_limit = self.limit - 320 * (pages - 1)
                if local_limit == 0:
                    break

            headers = {
                "User-Agent": "RezarTheSerg/1.0 (by e621User)",
            }
            params = {
                "tags": " ".join(tags),
                "limit": local_limit,
                "page": page
            }
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                auth=(self.api_user, self.api_key)
            )
            response.raise_for_status()
            posts = response.json().get("posts", [])
            all_posts.extend(posts)

            # Если постов меньше, чем запрошено — значит, дальше ничего нет
            if len(posts) < local_limit:
                break

        return all_posts