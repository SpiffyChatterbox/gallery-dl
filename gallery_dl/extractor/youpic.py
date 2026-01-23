# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://youpic.com/"""

from .common import Extractor, Message
from .. import text, dt


class YoupicExtractor(Extractor):
    """Base class for youpic extractors"""
    category = "youpic"
    root = "https://youpic.com"
    root_api = "https://old.youpic.com"
    directory_fmt = ("{category}", "{user[name]}")
    filename_fmt = "{id}_{title}.{extension}"
    archive_fmt = "{id}"

    def _init(self):
        self.size = self.config("size", "huge")

    def _pagination(self, endpoint, params=None):
        """Handle cursor-based pagination"""
        url = f"{self.root_api}/api/{endpoint}"
        if params is None:
            params = {}

        while True:
            data = self.request(url, params=params).json()
            resources = data.get("resource", {})

            users = {u["id"]: u for u in resources.get("User", [])}
            images = resources.get("Image", [])

            for image in images:
                user_id = image.get("user")
                if user_id and user_id in users:
                    image["user"] = users[user_id]
                yield image

            if data.get("ended", True):
                break

            cursor = data.get("cursor")
            if not cursor:
                break
            params["cursor"] = cursor

    def _image_url(self, image):
        """Build image URL from image data"""
        url_data = image.get("url", {})
        base_url = url_data.get("url", f"{self.root}/y")
        file_hash = url_data.get("file", "")
        if file_hash:
            return f"{base_url}/{self.size}/{file_hash}"
        return None

    def _transform_image(self, image):
        """Transform API image data to metadata dict"""
        return {
            "id": image.get("id"),
            "title": image.get("title", ""),
            "description": image.get("description", ""),
            "slug": image.get("slug", ""),
            "tags": image.get("tags", []),
            "width": image.get("width"),
            "height": image.get("height"),
            "date": dt.parse_ts(image.get("created", 0) // 1000),
            "user": image.get("user", {}),
            "category_id": image.get("categoryId"),
            "region": image.get("region", ""),
            "location": image.get("location", {}),
            "nsfw": image.get("nsfw", False),
            "is_inspiration": image.get("isInspiration", False),
            "exif": {
                "camera": image.get("exifCamera", ""),
                "lens": image.get("exifLens", ""),
                "copyright": image.get("exifCopyright", ""),
                "taken": image.get("exifTaken", ""),
                "exposure": image.get("exifExposure", ""),
                "focal": image.get("exifFocal", ""),
                "aperture": image.get("exifAperture", ""),
                "iso": image.get("exifIso", ""),
            },
            "count": image.get("count", {}),
        }


class YoupicUserExtractor(YoupicExtractor):
    """Extractor for a user's photos on youpic.com"""
    subcategory = "user"
    pattern = (r"(?:https?://)?(?:www\.)?youpic\.com"
               r"/(?!photo/|image/|inspiration|hot|newest|explore)"
               r"([^/?#]+)/?$")
    example = "https://youpic.com/USERNAME"

    def __init__(self, match):
        YoupicExtractor.__init__(self, match)
        self.username = match.group(1)

    def items(self):
        # Get user ID from the main page
        url = f"{self.root}/{self.username}"
        page = self.request(url).text

        # Extract user ID from og:image meta tag
        # Format: https://youpic.com/card/user/USER_ID
        card_url = text.extr(
            page, 'name="og:image" content="', '"')
        if not card_url:
            card_url = text.extr(
                page, 'name="image" content="', '"')

        user_id = card_url.rpartition("/")[2] if card_url else None
        if not user_id:
            self.log.error("Could not find user ID for '%s'", self.username)
            return

        first = True
        for image in self._pagination(f"user/{user_id}/pic"):
            data = self._transform_image(image)
            url = self._image_url(image)

            if not url:
                continue

            if first:
                first = False
                yield Message.Directory, "", data
            yield Message.Url, url, text.nameext_from_url(url, data)


class YoupicImageExtractor(YoupicExtractor):
    """Extractor for individual images on youpic.com"""
    subcategory = "image"
    pattern = (r"(?:https?://)?(?:www\.)?youpic\.com"
               r"/(?:photo|image)/(\d+)")
    example = "https://youpic.com/photo/12345"

    def __init__(self, match):
        YoupicExtractor.__init__(self, match)
        self.image_id = match.group(1)

    def items(self):
        url = f"{self.root_api}/api/image/{self.image_id}"
        response = self.request(url).json()

        # Single image API returns User/Image at top level
        users = {u["id"]: u for u in response.get("User", [])}
        images = response.get("Image", [])

        if not images:
            self.log.error("Image %s not found", self.image_id)
            return

        image = images[0]
        user_id = image.get("user")
        if user_id and user_id in users:
            image["user"] = users[user_id]

        data = self._transform_image(image)
        url = self._image_url(image)

        if url:
            yield Message.Directory, "", data
            yield Message.Url, url, text.nameext_from_url(url, data)


class YoupicInspirationExtractor(YoupicExtractor):
    """Extractor for the inspiration feed on youpic.com"""
    subcategory = "inspiration"
    pattern = r"(?:https?://)?(?:www\.)?youpic\.com/inspiration/?$"
    example = "https://youpic.com/inspiration"

    def items(self):
        first = True
        for image in self._pagination("inspiration"):
            data = self._transform_image(image)
            url = self._image_url(image)

            if not url:
                continue

            if first:
                first = False
                yield Message.Directory, "", data
            yield Message.Url, url, text.nameext_from_url(url, data)


class YoupicNewestExtractor(YoupicExtractor):
    """Extractor for the newest photos feed on youpic.com"""
    subcategory = "newest"
    pattern = r"(?:https?://)?(?:www\.)?youpic\.com/newest/?$"
    example = "https://youpic.com/newest"

    def items(self):
        first = True
        for image in self._pagination("newest"):
            data = self._transform_image(image)
            url = self._image_url(image)

            if not url:
                continue

            if first:
                first = False
                yield Message.Directory, "", data
            yield Message.Url, url, text.nameext_from_url(url, data)
