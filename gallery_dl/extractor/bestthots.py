# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://bestthots.com/"""

from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?bestthots\.com"


class BestthotsExtractor(Extractor):
    """Base class for bestthots extractors"""
    category = "bestthots"
    root = "https://bestthots.com"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{id}.{extension}"
    archive_fmt = "{id}"


class BestthotsModelExtractor(BestthotsExtractor):
    """Extractor for bestthots model pages"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/([^/?#]+)/?$"
    example = "https://bestthots.com/MODEL"

    def __init__(self, match):
        BestthotsExtractor.__init__(self, match)
        self.model = match.group(1)

    def items(self):
        data = {"model": self.model}
        yield Message.Directory, "", data

        for post in self._pagination():
            post["model"] = self.model
            url = post.get("url")
            if url:
                yield Message.Url, url, post

    def _pagination(self):
        url = f"{self.root}/{self.model}"
        headers = {"X-Requested-With": "XMLHttpRequest"}
        params = {"page": 1, "type": "all"}

        while True:
            posts = self.request(url, headers=headers, params=params).json()
            if not posts:
                return

            for post in posts:
                yield self._process_post(post)

            if len(posts) < 48:
                return
            params["page"] += 1

    def _process_post(self, post):
        data = {
            "id": post.get("get_id") or post.get("idx"),
            "date": self.parse_datetime(
                post.get("published_date"), "%Y-%m-%d %H:%M:%S"),
        }

        if post.get("type") == 1:
            # Video
            data["url"] = "ytdl:" + post.get("stream_url_play", "")
            data["extension"] = "mp4"
        else:
            # Image
            data["url"] = post.get("image", "")
            text.nameext_from_url(data["url"], data)

        return data


class BestthotsPostExtractor(BestthotsExtractor):
    """Extractor for individual bestthots posts"""
    subcategory = "post"
    pattern = BASE_PATTERN + r"/([^/?#]+)/(\d+)"
    example = "https://bestthots.com/MODEL/12345"

    def __init__(self, match):
        BestthotsExtractor.__init__(self, match)
        self.model = match.group(1)
        self.post_id = match.group(2)

    def items(self):
        url = f"{self.root}/{self.model}/{self.post_id}"
        page = self.request(url).text

        # Extract image URL (data-fancybox src= for images)
        image_url = text.extr(page, 'data-fancybox src="', '"')

        # Check if it's a video (look for video source)
        if not image_url:
            video_src = text.extr(page, '<source src="', '"')
            if video_src:
                image_url = "ytdl:" + video_src

        data = {
            "model": self.model,
            "id": text.parse_int(self.post_id),
        }

        if image_url and image_url.startswith("ytdl:"):
            data["url"] = image_url
            data["extension"] = "mp4"
        elif image_url:
            data["url"] = image_url
            text.nameext_from_url(image_url, data)
        else:
            data["url"] = ""

        yield Message.Directory, "", data
        if data["url"]:
            yield Message.Url, data["url"], data
