# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.onlybestgals.com/"""

from .common import Extractor, FlareSolverrMixin, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?onlybestgals\.com"


class OnlybestgalsExtractor(FlareSolverrMixin, Extractor):
    """Base class for onlybestgals extractors"""
    category = "onlybestgals"
    root = "https://www.onlybestgals.com"
    cookies_domain = ".onlybestgals.com"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{num}.{extension}"
    archive_fmt = "{model}_{num}"


class OnlybestgalsModelExtractor(OnlybestgalsExtractor):
    """Extractor for model pages on onlybestgals.com"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/model/([a-z0-9_-]+-[a-zA-Z0-9]{5})/"
    example = "https://www.onlybestgals.com/model/tawny-swain-9t0ky/"

    def __init__(self, match):
        OnlybestgalsExtractor.__init__(self, match)
        self.model_hash = match.group(1)

    def items(self):
        url = "{}/model/{}/".format(self.root, self.model_hash)
        page = self.request(url).text

        # Extract model name from h1
        model = text.extr(page, '<h1', '</h1>')
        if model:
            model = text.extr(model, '>', '')
            # Clean up: "Tawny Swain tawny-swain OnlyFans Leaks 2025"
            # Remove common suffixes
            for suffix in (' OnlyFans Leaks', ' Nude', ' Leaked'):
                if suffix in model:
                    model = model.split(suffix)[0]
            # Remove slug if duplicated at end
            parts = model.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].replace('-', '').lower() == \
                    parts[0].replace(' ', '').lower():
                model = parts[0]
        if not model:
            # Extract from slug: tawny-swain-9t0ky -> Tawny Swain
            model = self.model_hash.rsplit('-', 1)[0].replace('-', ' ').title()

        data = {
            "model": model.strip(),
            "model_hash": self.model_hash,
        }

        yield Message.Directory, "", data

        # Find all thumbnail images and convert to full size
        seen = set()
        num = 0
        for thumb_url in text.extract_iter(
                page, 'src="https://www.onlybestgals.com/images/', '"'):
            thumb_url = "https://www.onlybestgals.com/images/" + thumb_url
            if '-460px.' in thumb_url and thumb_url not in seen:
                seen.add(thumb_url)
                # Convert to 1080px version
                full_url = thumb_url.replace('-460px.', '-1080px.')
                num += 1
                img_data = text.nameext_from_url(full_url, data.copy())
                img_data["num"] = num
                img_data["_fallback"] = (thumb_url,)
                yield Message.Url, full_url, img_data

        # Also check data-src for lazy-loaded images
        for thumb_url in text.extract_iter(
                page, 'data-src="https://www.onlybestgals.com/images/', '"'):
            thumb_url = "https://www.onlybestgals.com/images/" + thumb_url
            if '-460px.' in thumb_url and thumb_url not in seen:
                seen.add(thumb_url)
                full_url = thumb_url.replace('-460px.', '-1080px.')
                num += 1
                img_data = text.nameext_from_url(full_url, data.copy())
                img_data["num"] = num
                img_data["_fallback"] = (thumb_url,)
                yield Message.Url, full_url, img_data


class OnlybestgalsCategoryExtractor(OnlybestgalsExtractor):
    """Extractor for category pages on onlybestgals.com"""
    subcategory = "category"
    pattern = BASE_PATTERN + r"/(new-models|random)(?:/(\d+))?/"
    example = "https://www.onlybestgals.com/new-models/"

    def __init__(self, match):
        OnlybestgalsExtractor.__init__(self, match)
        self.category_name = match.group(1)
        self.page_num = text.parse_int(match.group(2), 1)

    def items(self):
        data = {"_extractor": OnlybestgalsModelExtractor}
        page_num = self.page_num

        while True:
            if page_num == 1:
                url = "{}/{}/".format(self.root, self.category_name)
            else:
                url = "{}/{}/{}/".format(
                    self.root, self.category_name, page_num)

            page = self.request(url).text

            # Find model page links: /model/slug-HASH/
            found = False
            for href in text.extract_iter(page, 'href="/model/', '"'):
                href = href.rstrip('/')
                # Verify it has the 5-char hash pattern
                if ('-' in href[-6:] and
                        href.rsplit('-', 1)[-1].isalnum() and
                        len(href.rsplit('-', 1)[-1]) == 5):
                    found = True
                    yield Message.Queue, self.root + '/model/' + href + '/', \
                        data

            if not found:
                return

            # Check for next page
            next_page = "/{}/{}/".format(self.category_name, page_num + 1)
            if next_page not in page:
                return
            page_num += 1
