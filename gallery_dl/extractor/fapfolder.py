# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://fapfolder.club/"""

from .common import Extractor, Message
from .. import text, exception


BASE_PATTERN = r"(?:https?://)?(?:www\.)?fapfolder\.club"


class FapfolderExtractor(Extractor):
    """Base class for fapfolder extractors"""
    category = "fapfolder"
    root = "https://fapfolder.club"


class FapfolderPhotoExtractor(FapfolderExtractor):
    """Extractor for individual photos on fapfolder.club"""
    subcategory = "photo"
    directory_fmt = ("{category}", "{group}")
    filename_fmt = "{group}_{id}.{extension}"
    archive_fmt = "photo_{group}_{id}"
    pattern = BASE_PATTERN + r"/photos/(\d+)"
    example = "https://fapfolder.club/photos/123456"

    def __init__(self, match):
        FapfolderExtractor.__init__(self, match)
        self.photo_id = match.group(1)

    def items(self):
        url = f"{self.root}/photos/{self.photo_id}"
        page = self.request(url).text

        # Extract the full-size image URL from data-image attribute
        image_url = text.extr(page, 'data-image="', '"')
        if not image_url:
            raise exception.NotFoundError("photo")

        # Extract group/performer name from the page
        group = text.extr(page, 'href="https://fapfolder.club/groups/', '"')
        if not group:
            group = "unknown"

        data = {
            "id": text.parse_int(self.photo_id),
            "group": group,
        }

        yield Message.Directory, data
        yield Message.Url, image_url, text.nameext_from_url(image_url, data)


class FapfolderGroupExtractor(FapfolderExtractor):
    """Extractor for all photos from a fapfolder group/performer"""
    subcategory = "group"
    pattern = BASE_PATTERN + r"/groups/([^/?#]+)(?:/photos)?/?$"
    example = "https://fapfolder.club/groups/performer"

    def __init__(self, match):
        FapfolderExtractor.__init__(self, match)
        self.group = match.group(1)

    def items(self):
        url = f"{self.root}/groups/{self.group}"
        page = self.request(url).text

        # Extract all photo URLs from the page
        # Photos are in <a class="pg_photo js_lightbox" href="/photos/ID">
        for photo_url in text.extract_iter(
                page, 'class="pg_photo  js_lightbox" href="', '"'):
            if photo_url.startswith("https://fapfolder.club/photos/"):
                yield Message.Queue, photo_url, {
                    "_extractor": FapfolderPhotoExtractor}
            elif photo_url.startswith("/photos/"):
                full_url = f"{self.root}{photo_url}"
                yield Message.Queue, full_url, {
                    "_extractor": FapfolderPhotoExtractor}


class FapfolderUserExtractor(FapfolderExtractor):
    """Extractor for all photos uploaded by a user"""
    subcategory = "user"
    pattern = BASE_PATTERN + r"/([^/?#]+)/?$"
    example = "https://fapfolder.club/username"

    def __init__(self, match):
        FapfolderExtractor.__init__(self, match)
        self.username = match.group(1)

    def items(self):
        # Skip if it's actually a group URL
        if self.username == "groups":
            return

        url = f"{self.root}/{self.username}"
        page = self.request(url).text

        # Extract all photo URLs from user's posts
        for photo_url in text.extract_iter(
                page, 'class="pg_photo  js_lightbox" href="', '"'):
            if photo_url.startswith("https://fapfolder.club/photos/"):
                yield Message.Queue, photo_url, {
                    "_extractor": FapfolderPhotoExtractor}
            elif photo_url.startswith("/photos/"):
                full_url = f"{self.root}{photo_url}"
                yield Message.Queue, full_url, {
                    "_extractor": FapfolderPhotoExtractor}
