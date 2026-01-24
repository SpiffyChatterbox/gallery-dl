# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://nudostar.tv/"""

from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:[a-z]{2}.)?nudostar\.tv"


class NudostarExtractor(Extractor):
    """Base class for NudoStar extractors"""
    category = "nudostar"
    root = "https://nudostar.tv"

    def _init(self):
        self.session.headers["Referer"] = self.root + "/"


class NudostarModelExtractor(NudostarExtractor):
    """Extractor for NudoStar models"""
    subcategory = "model"
    directory_fmt = ("{category}", "{model_slug}")
    filename_fmt = "{model_slug}_{num:>04}.{extension}"
    archive_fmt = "{model_slug}_{num}"
    pattern = rf"{BASE_PATTERN}/models/([^/?#]+)/?(?:next-\d+)?/?$"
    example = "https://nudostar.tv/models/MODEL/"

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.model_slug = match.group(1)

    def items(self):
        url = f"{self.root}/models/{self.model_slug}/"
        page = self.request(url).text
        data = self._extract_metadata(page)

        yield Message.Directory, "", data

        for img_url, img_data in self._pagination(page, data):
            yield Message.Url, img_url, img_data

    def _extract_metadata(self, page):
        names = text.extr(page, "<title>", "<").rpartition(
            " Nude ")[0].split(" / ")

        return {
            "model_slug" : self.model_slug,
            "model_names": names,
            "model"      : names[0] if names else self.model_slug,
        }

    def _pagination(self, page, data):
        seen = set()

        while True:
            # Extract only main content, exclude related-videos section
            content = text.extr(
                page, '<div class="list-videos">', '<div class="related-')
            if not content:
                content = page

            for thumb in text.extract_iter(
                    content, 'src="https://nudostar.tv/contents/', '"'):
                # Convert thumbnail to full-size image
                full = thumb.replace("_320px", "")
                img_url = f"{self.root}/contents/{full}"

                if img_url in seen:
                    continue
                seen.add(img_url)

                # Extract image number from filename
                num = text.parse_int(
                    full.rpartition("_")[2].partition(".")[0])

                img_data = text.nameext_from_url(img_url, data.copy())
                img_data["num"] = num
                yield img_url, img_data

            # Check for next page
            next_url = text.extr(page, 'class="next"><a href="', '"')
            if not next_url:
                return
            page = self.request(next_url).text


class NudostarImageExtractor(NudostarExtractor):
    """Extractor for NudoStar images"""
    subcategory = "image"
    directory_fmt = ("{category}", "{model_slug}")
    filename_fmt = "{model_slug}_{num:>04}.{extension}"
    archive_fmt = "{model_slug}_{num}"
    pattern = rf"{BASE_PATTERN}/models/([^/?#]+)/(\d+)/?$"
    example = "https://nudostar.tv/models/MODEL/123/"

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.model_slug = match.group(1)
        self.image_num = match.group(2)

    def items(self):
        url = f"{self.root}/models/{self.model_slug}/{self.image_num}/"
        page = self.request(url, notfound=self.subcategory).text

        img_url = text.extract(
            page, 'src="', '"', page.index('class="headline"'))[0]

        names = text.extr(page, "<title>", "<").rpartition(
            " Nude ")[0].split(" / ")

        data = {
            "model_slug" : self.model_slug,
            "model_names": names,
            "model"      : names[0] if names else self.model_slug,
            "num"        : text.parse_int(self.image_num),
        }
        data = text.nameext_from_url(img_url, data)

        yield Message.Directory, "", data
        yield Message.Url, img_url, data
