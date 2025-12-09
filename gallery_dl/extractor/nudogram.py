# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://nudogram.com/"""

from .common import GalleryExtractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?nudogram\.com"


class NudogramExtractor(GalleryExtractor):
    """Base class for Nudogram extractors"""
    category = "nudogram"
    root = "https://nudogram.com"


class NudogramModelExtractor(NudogramExtractor):
    """Extractor for Nudogram models"""
    subcategory = "model"
    pattern = rf"{BASE_PATTERN}(/models/([^/?#]+)/?)$"
    example = "https://nudogram.com/models/MODEL/"

    def metadata(self, page):
        name = text.extr(page, "<title>", " Nude")
        slug = self.groups[1]

        return {
            "gallery_id" : slug,
            "model_slug" : slug,
            "model"      : name.strip() if name else slug,
            "title"      : "",
        }

    def images(self, page):
        # Thumbnails are numbered in descending order, first one = total count
        path = text.extr(page, 'src="https://nudogram.com/contents/', '"')
        if not path:
            return []

        # Path format: e/k/model-slug/1000/model-slug_0397_280.jpg
        # We need: e/k/model-slug/1000/model-slug_0001.jpg (full size)
        # Split: base_path='...model-slug', num='0397', thumb='280.jpg'
        base_path, num, _ = path.rsplit("_", 2)
        count = text.parse_int(num)
        ext = ".jpg"

        base = f"{self.root}/contents/{base_path}_"

        return [
            (f"{base}{i:04}{ext}", None)
            for i in range(1, count + 1)
        ]


class NudogramImageExtractor(NudogramExtractor):
    """Extractor for Nudogram individual images"""
    subcategory = "image"
    pattern = rf"{BASE_PATTERN}(/models/([^/?#]+)/(\d+)/?)$"
    example = "https://nudogram.com/models/MODEL/123/"

    def items(self):
        model_slug, num = self.groups[1], self.groups[2]
        url = f"{self.root}/models/{model_slug}/{num}/"
        page = self.request(url, notfound=self.subcategory).text

        # Find the full-size image (class="img-content")
        img_url = text.extr(
            page, 'class="img-content" src="', '"')

        name = text.extr(page, "<title>", " OnlyFans")

        data = {
            "gallery_id" : model_slug,
            "model_slug" : model_slug,
            "model"      : name.strip() if name else model_slug,
            "num"        : text.parse_int(num),
        }
        data = text.nameext_from_url(img_url, data)
        data["url"] = img_url

        yield Message.Directory, "", data
        yield Message.Url, img_url, data
