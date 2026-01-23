# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://porn7.net/"""

from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?porn7\.net"


class Porn7Extractor(Extractor):
    """Base class for porn7 extractors"""
    category = "porn7"
    root = "https://porn7.net"
    directory_fmt = ("{category}",)
    filename_fmt = "{id}_{title[:80]}.{extension}"
    archive_fmt = "{id}"
    request_interval = (1.0, 2.0)

    def _pagination(self, url):
        """Handle page-based pagination"""
        page_num = 1

        while True:
            page = self.request(f"{url}?page={page_num}").text

            post_urls = list(text.extract_iter(
                page, 'href="https://porn7.net/post/', '"'))

            if not post_urls:
                return

            for post_url in post_urls:
                post_url = post_url.partition("?")[0]
                yield self.root + "/post/" + post_url

            page_num += 1


class Porn7PostExtractor(Porn7Extractor):
    """Extractor for individual posts on porn7.net"""
    subcategory = "post"
    pattern = BASE_PATTERN + r"/post/([^/?#]+)-(\d+)"
    example = "https://porn7.net/post/title-12345"

    def __init__(self, match):
        Porn7Extractor.__init__(self, match)
        self.slug = match.group(1)
        self.post_id = match.group(2)

    def items(self):
        url = f"{self.root}/post/{self.slug}-{self.post_id}"
        page = self.request(url).text

        title = text.unescape(text.extr(
            page, "<title>", "</title>") or "").strip()

        # Find the main image (first sh-section__image in stamp section)
        # The main image is after col-lg-6 sh-section__item stamp
        stamp_pos = page.find("stamp")
        if stamp_pos != -1:
            main_content = page[stamp_pos:stamp_pos + 5000]
        else:
            main_content = page

        image_url = None
        video_url = None

        # Look for image - first one after stamp is the main image
        img_start = main_content.find('class="sh-section__image">')
        if img_start != -1:
            img_section = main_content[img_start:img_start + 500]
            image_url = text.extr(img_section, 'src="', '"')
            # Filter out thumbnails
            if image_url and "/thumbnails/" in image_url:
                image_url = None

        # Look for video
        video_start = main_content.find('<video')
        if video_start != -1:
            video_section = main_content[video_start:video_start + 1000]
            video_url = text.extr(video_section, '<source src="', '"')
            if not image_url:
                image_url = text.extr(video_section, 'poster="', '"')

        data = {
            "id": text.parse_int(self.post_id),
            "title": title,
            "slug": self.slug,
        }

        yield Message.Directory, "", data

        if video_url:
            yield Message.Url, video_url, text.nameext_from_url(
                video_url, data)
        elif image_url:
            yield Message.Url, image_url, text.nameext_from_url(
                image_url, data)


class Porn7CategoryExtractor(Porn7Extractor):
    """Extractor for porn7 category pages"""
    subcategory = "category"
    pattern = BASE_PATTERN + r"/category/([^/?#]+)"
    example = "https://porn7.net/category/breasts"

    def __init__(self, match):
        Porn7Extractor.__init__(self, match)
        self.category_name = match.group(1)

    def items(self):
        url = f"{self.root}/category/{self.category_name}"

        for post_url in self._pagination(url):
            yield Message.Queue, post_url, {"_extractor": Porn7PostExtractor}


class Porn7SearchExtractor(Porn7Extractor):
    """Extractor for porn7 search results"""
    subcategory = "search"
    pattern = BASE_PATTERN + r"/search\?q=([^&#]+)"
    example = "https://porn7.net/search?q=test"

    def __init__(self, match):
        Porn7Extractor.__init__(self, match)
        self.query = match.group(1)

    def items(self):
        url = f"{self.root}/search?q={self.query}"

        for post_url in self._pagination(url):
            yield Message.Queue, post_url, {"_extractor": Porn7PostExtractor}
