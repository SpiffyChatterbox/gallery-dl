# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.feetplaza.com/"""

from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?feetplaza\.com"


class FeetplazaExtractor(Extractor):
    """Base class for feetplaza extractors"""
    category = "feetplaza"
    root = "https://www.feetplaza.com"
    cookies_domain = ".feetplaza.com"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{post_id}_{filename}.{extension}"
    archive_fmt = "{post_id}"

    def _init(self):
        self.flaresolverr = self.config("flaresolverr")

    def request(self, url, **kwargs):
        """Override request to use FlareSolverr if configured."""
        if self.flaresolverr:
            return self._flaresolverr_request(url, **kwargs)
        return Extractor.request(self, url, **kwargs)

    def _flaresolverr_request(self, url, method="GET", **kwargs):
        """Make request through FlareSolverr."""
        payload = {
            "cmd": "request.get" if method == "GET" else "request.post",
            "url": url,
            "maxTimeout": 60000,
        }

        response = Extractor.request(
            self,
            f"{self.flaresolverr}/v1",
            method="POST",
            json=payload,
        )

        data = response.json()

        if data.get("status") != "ok":
            raise Exception(f"FlareSolverr error: {data.get('message')}")

        # Create a response-like object with the HTML
        class FlareSolverrResponse:
            def __init__(self, solution):
                self.text = solution["response"]
                self.status_code = solution["status"]
                self.url = solution["url"]
                self.headers = solution.get("headers", {})

        return FlareSolverrResponse(data["solution"])

    def _pagination(self, url):
        """Paginate through post listings"""
        while True:
            page = self.request(url).text

            for item in text.extract_iter(
                    page, 'class="g1-frame" href="', '"'):
                # Skip category and model links
                if "/category/" not in item and "/models/" not in item:
                    yield item

            # Find next page
            next_url = text.extr(page, 'next" href="', '"')
            if not next_url:
                return
            url = text.unescape(next_url)


class FeetplazaPostExtractor(FeetplazaExtractor):
    """Extractor for individual feetplaza posts"""
    subcategory = "post"
    pattern = (BASE_PATTERN +
               r"/([a-z0-9_-]+)/(\d+)/([a-z0-9_-]+)/?$")
    example = "https://www.feetplaza.com/naomi/292412/perfect-feet/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.model_slug = match.group(1)
        self.post_id = match.group(2)
        self.title_slug = match.group(3)

    def items(self):
        url = "{}/{}/{}/{}/".format(
            self.root, self.model_slug, self.post_id, self.title_slug)
        page = self.request(url).text

        # Extract image URL from og:image meta tag (most reliable)
        img_url = text.extr(page, 'og:image" content="', '"')

        if not img_url:
            # Fallback: try entry-content section
            entry = text.extr(page, 'class="entry-content"', '</article>')
            if entry:
                img_url = text.extr(entry, 'src="', '"')

        if not img_url:
            # Fallback: try srcset for larger image
            srcset = text.extr(page, 'entry-content', '</article>')
            if srcset:
                srcset = text.extr(srcset, 'srcset="', '"')
                if srcset:
                    # Get the largest image (last in srcset)
                    urls = srcset.split(", ")
                    if urls:
                        img_url = urls[-1].partition(" ")[0]

        if not img_url:
            return

        # Remove size suffix to get full image
        # e.g., soles39-758x673.jpg -> soles39.jpg
        full_url = self._get_full_size_url(img_url)

        # Extract model name from page (use meta author tag - most reliable)
        model = text.extr(page, 'name="author" content="', '"')
        if not model:
            # Fallback: extract from itemprop name
            model = text.extr(page, 'itemprop="name">', '</span>')
        if not model:
            model = self.model_slug

        # Extract title
        title = text.extr(page, '<title>', '</title>')
        if title:
            title = text.unescape(title.partition(" - ")[0])
        else:
            title = self.title_slug.replace("-", " ").title()

        data = {
            "model": model,
            "model_slug": self.model_slug,
            "post_id": text.parse_int(self.post_id),
            "title": title,
            "title_slug": self.title_slug,
        }
        data = text.nameext_from_url(full_url, data)
        data["_fallback"] = (img_url,)

        yield Message.Directory, "", data
        yield Message.Url, full_url, data

    def _get_full_size_url(self, url):
        """Remove WordPress size suffix from URL"""
        # Pattern: name-WIDTHxHEIGHT.ext -> name.ext
        path = text.nameext_from_url(url)["filename"]
        # Check if filename ends with -NNNxNNN
        if "-" in path:
            base, _, size = path.rpartition("-")
            if "x" in size and size.replace("x", "").isdigit():
                return url.replace(f"-{size}", "")
        return url


class FeetplazaModelExtractor(FeetplazaExtractor):
    """Extractor for feetplaza model pages"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/models/([a-z0-9_-]+)/?$"
    example = "https://www.feetplaza.com/models/naomi/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.model_slug = match.group(1)

    def items(self):
        url = f"{self.root}/models/{self.model_slug}/"
        data = {"_extractor": FeetplazaPostExtractor}

        for post_url in self._pagination(url):
            yield Message.Queue, post_url, data


class FeetplazaCategoryExtractor(FeetplazaExtractor):
    """Extractor for feetplaza category pages"""
    subcategory = "category"
    pattern = BASE_PATTERN + r"/category/([a-z0-9_-]+)/?$"
    example = "https://www.feetplaza.com/category/soles/"

    def __init__(self, match):
        FeetplazaExtractor.__init__(self, match)
        self.category_slug = match.group(1)

    def items(self):
        url = f"{self.root}/category/{self.category_slug}/"
        data = {"_extractor": FeetplazaPostExtractor}

        for post_url in self._pagination(url):
            yield Message.Queue, post_url, data
