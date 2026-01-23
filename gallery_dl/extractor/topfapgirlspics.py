# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.topfapgirlspics.com/"""

from .common import Extractor, FlareSolverrMixin, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?topfapgirlspics\.com"


class TopfapgirlspicsExtractor(FlareSolverrMixin, Extractor):
    """Base class for topfapgirlspics extractors"""
    category = "topfapgirlspics"
    root = "https://www.topfapgirlspics.com"
    cookies_domain = ".topfapgirlspics.com"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{id}.{extension}"
    archive_fmt = "{id}"


class TopfapgirlspicsPhotoExtractor(TopfapgirlspicsExtractor):
    """Extractor for individual photos on topfapgirlspics.com"""
    subcategory = "photo"
    pattern = BASE_PATTERN + r"/([a-z0-9_-]+)/t/(\d+)/"
    example = "https://www.topfapgirlspics.com/tisha-alyn/t/28918959023391/"

    def __init__(self, match):
        TopfapgirlspicsExtractor.__init__(self, match)
        self.model_slug = match.group(1)
        self.photo_id = match.group(2)

    def items(self):
        url = "{}/{}/t/{}/".format(self.root, self.model_slug, self.photo_id)
        page = self.request(url).text

        # Find the 1080px image URL
        image_url = text.extr(page, 'href="', '"',
                              page.find('-1080px.jpg') - 200)
        if not image_url or '-1080px' not in image_url:
            # Fallback: search for img src with 1080px
            image_url = text.extr(page, 'src="', '"',
                                  page.find('-1080px.jpg') - 100)

        if not image_url or '-1080px' not in image_url:
            # Try broader search
            import re
            match = re.search(
                r'(https://www\.topfapgirlspics\.com'
                r'/content/[^"]+1080px\.jpg)', page)
            if match:
                image_url = match.group(1)

        if not image_url:
            return

        # Extract model name from h1
        model = text.extr(page, '<h1', '</h1>')
        if model:
            model = text.extr(model, '>', '')
            # Clean up: "Tisha Alyn tisha-alyn Nude" -> "Tisha Alyn"
            model = model.split(' Nude')[0]
            # Remove slug if duplicated
            parts = model.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].replace('-', ' ').lower() == \
                    parts[0].lower():
                model = parts[0]
        if not model:
            model = self.model_slug.replace('-', ' ').title()

        data = {
            "model": model.strip(),
            "model_slug": self.model_slug,
            "id": self.photo_id,
        }

        yield Message.Directory, "", data
        yield Message.Url, image_url, text.nameext_from_url(image_url, data)


class TopfapgirlspicsModelExtractor(TopfapgirlspicsExtractor):
    """Extractor for model pages on topfapgirlspics.com"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/([a-z0-9_-]+-[a-zA-Z0-9]{5})/"
    example = "https://www.topfapgirlspics.com/tisha-alyn-o9URj/"

    def __init__(self, match):
        TopfapgirlspicsExtractor.__init__(self, match)
        self.model_hash = match.group(1)

    def items(self):
        url = "{}/{}/".format(self.root, self.model_hash)
        page = self.request(url).text

        data = {"_extractor": TopfapgirlspicsPhotoExtractor}

        # Extract photo page links: /model-slug/t/ID/
        for photo_url in text.extract_iter(page, 'href="/', '"'):
            if '/t/' in photo_url and photo_url.endswith('/'):
                yield Message.Queue, self.root + '/' + photo_url, data


class TopfapgirlspicsCategoryExtractor(TopfapgirlspicsExtractor):
    """Extractor for category pages on topfapgirlspics.com"""
    subcategory = "category"
    pattern = BASE_PATTERN + r"/(new|random)(?:/(\d+))?/"
    example = "https://www.topfapgirlspics.com/new/"

    def __init__(self, match):
        TopfapgirlspicsExtractor.__init__(self, match)
        self.category_name = match.group(1)
        self.page_num = text.parse_int(match.group(2), 1)

    def items(self):
        data = {"_extractor": TopfapgirlspicsModelExtractor}
        page_num = self.page_num

        while True:
            if page_num == 1:
                url = "{}/{}/".format(self.root, self.category_name)
            else:
                url = "{}/{}/{}/".format(
                    self.root, self.category_name, page_num)

            page = self.request(url).text

            # Find model page links (ending with 5-char hash)
            found = False
            for href in text.extract_iter(page, 'href="/', '"'):
                # Strip trailing slash and match model-slug-HASH pattern
                href = href.rstrip('/')
                if (href.count('/') == 0 and
                        len(href) >= 7 and
                        '-' in href[-6:] and
                        href.rsplit('-', 1)[-1].isalnum() and
                        len(href.rsplit('-', 1)[-1]) == 5):
                    found = True
                    yield Message.Queue, self.root + '/' + href + '/', data

            if not found:
                return

            # Check for next page
            next_page = "/{}/{}/".format(self.category_name, page_num + 1)
            if next_page not in page:
                return
            page_num += 1
