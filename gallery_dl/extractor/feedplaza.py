# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.feetplaza.com/"""

from .common import Extractor, Message
from .. import text, exception


BASE_PATTERN = r"(?:https?://)?(?:www\.)?feetplaza\.com"


class FeetplazaExtractor(Extractor):
    """Base class for feetplaza extractors"""
    category = "feetplaza"
    root = "https://www.feetplaza.com"


class FeetplazaPostExtractor(FeetplazaExtractor):
    """Extractor for individual posts on feetplaza.com"""
    subcategory = "post"
    directory_fmt = ("{category}", "{post_category}", "{model|}")
    filename_fmt = "{category}_{post_id}_{num:>03}.{extension}"
    archive_fmt = "{post_id}_{num}"
    pattern = BASE_PATTERN + r"/([^/]+)/(\d+)/([^/?#]+)"
    example = "https://www.feetplaza.com/CATEGORY/12345/POST-TITLE/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.post_category = match.group(1)
        self.post_id = match.group(2)
        self.post_slug = match.group(3)

    def items(self):
        url = "{}/{}/{}/{}/".format(
            self.root, self.post_category, self.post_id, self.post_slug)
        page = self.request(url).text

        # Extract post content area
        content = text.extr(
            page, '<div class="entry-content', '</div>')
        if not content:
            raise exception.NotFoundError("post")

        # Extract metadata
        title = text.unescape(
            text.extr(page, '<meta property="og:title" content="', '"') or
            text.extr(page, '<title>', '</title>') or "")

        # Try to extract model name from various sources
        model = (
            text.extr(page, '/models/', '/') or
            text.extr(page, 'Model:', '<') or
            text.extr(content, 'model:', '<') or
            ""
        )

        data = {
            "post_id": text.parse_int(self.post_id),
            "post_category": self.post_category,
            "post_slug": self.post_slug,
            "title": title.strip(),
            "model": model.strip(),
        }

        # Extract images from wp-content/uploads
        images = []
        for img in text.extract_iter(content, '<img', '>'):
            img_url = text.extr(img, 'src="', '"')
            if img_url and '/wp-content/uploads/' in img_url:
                # Remove thumbnail suffix (e.g., -265x375.jpg)
                # to get full-size image
                path, _, end = img_url.rpartition('-')
                if 'x' in end and end.replace('x', '').replace(
                        '.jpg', '').replace('.png', '').isdigit():
                    # This is a thumbnail, reconstruct full size
                    extension = end.rpartition('.')[2]
                    img_url = "{}.{}".format(path, extension)
                images.append(img_url)

        if not images:
            self.log.warning("No images found in post %s", self.post_id)
            return

        yield Message.Directory, data
        for num, img_url in enumerate(images, 1):
            image_data = text.nameext_from_url(img_url, data)
            image_data["num"] = num
            yield Message.Url, img_url, image_data


class FeetplazaModelExtractor(FeetplazaExtractor):
    """Extractor for all posts from a feetplaza model"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/models/([^/?#]+)"
    example = "https://www.feetplaza.com/models/MODEL-NAME/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.model = match.group(1)

    def items(self):
        url = "{}/models/{}/".format(self.root, self.model)
        page = self.request(url).text

        # Queue all post URLs from this model page
        data = {"_extractor": FeetplazaPostExtractor}

        # Extract post links - WordPress typically uses article or post classes
        for article in text.extract_iter(
                page, '<article', '</article>'):
            post_url = text.extr(article, '<a href="', '"')
            if post_url and post_url.startswith(self.root):
                yield Message.Queue, post_url, data

        # Handle pagination
        page_num = 2
        while True:
            next_url = text.extr(page, 'class="next page-numbers" href="', '"')
            if not next_url:
                # Try alternate pagination pattern
                next_url = "{}/models/{}/page/{}/".format(
                    self.root, self.model, page_num)
                test_page = self.request(next_url, fatal=False)
                if test_page.status_code != 200:
                    break
                page = test_page.text
            else:
                page = self.request(next_url).text

            for article in text.extract_iter(
                    page, '<article', '</article>'):
                post_url = text.extr(article, '<a href="', '"')
                if post_url and post_url.startswith(self.root):
                    yield Message.Queue, post_url, data

            page_num += 1


class FeetplazaCategoryExtractor(FeetplazaExtractor):
    """Extractor for feetplaza category pages"""
    subcategory = "category"
    pattern = BASE_PATTERN + r"/category/(\d+)/([^/?#]+)"
    example = "https://www.feetplaza.com/category/01/CATEGORY-NAME/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.category_id = match.group(1)
        self.category_name = match.group(2)

    def items(self):
        url = "{}/category/{}/{}/".format(
            self.root, self.category_id, self.category_name)
        page = self.request(url).text

        # Queue all post URLs from this category
        data = {"_extractor": FeetplazaPostExtractor}

        # Extract post links
        for article in text.extract_iter(
                page, '<article', '</article>'):
            post_url = text.extr(article, '<a href="', '"')
            if post_url and post_url.startswith(self.root):
                yield Message.Queue, post_url, data

        # Handle pagination
        page_num = 2
        while True:
            next_url = text.extr(page, 'class="next page-numbers" href="', '"')
            if not next_url:
                # Try alternate pagination pattern
                next_url = "{}/category/{}/{}/page/{}/".format(
                    self.root, self.category_id,
                    self.category_name, page_num)
                test_page = self.request(next_url, fatal=False)
                if test_page.status_code != 200:
                    break
                page = test_page.text
            else:
                page = self.request(next_url).text

            for article in text.extract_iter(
                    page, '<article', '</article>'):
                post_url = text.extr(article, '<a href="', '"')
                if post_url and post_url.startswith(self.root):
                    yield Message.Queue, post_url, data

            page_num += 1
