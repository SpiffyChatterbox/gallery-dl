# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://viralxxxporn.com/"""

import urllib.parse
from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?viralxxxporn\.com"


class ViralxxxpornExtractor(Extractor):
    """Base class for viralxxxporn extractors"""
    category = "viralxxxporn"
    root = "https://viralxxxporn.com"
    request_interval = (1.0, 2.0)

    @staticmethod
    def _kvs_get_license_token(license_code):
        license_code = license_code.replace("$", "")
        license_values = [int(char) for char in license_code]

        modlicense = license_code.replace("0", "1")
        center = len(modlicense) // 2
        fronthalf = int(modlicense[:center + 1])
        backhalf = int(modlicense[center:])
        modlicense = str(
            4 * abs(fronthalf - backhalf))[:center + 1]

        return [
            (license_values[index + offset] + current) % 10
            for index, current in enumerate(map(int, modlicense))
            for offset in range(4)
        ]

    @classmethod
    def _kvs_get_real_url(cls, video_url, license_code):
        if not video_url.startswith("function/0/"):
            return video_url

        url = video_url[len("function/0/"):]
        parsed = urllib.parse.urlparse(url)
        license_token = cls._kvs_get_license_token(license_code)
        urlparts = parsed.path.split("/")

        hash_ = urlparts[3][:32]
        indices = list(range(32))

        accum = 0
        for src in reversed(range(32)):
            accum += license_token[src]
            dest = (src + accum) % 32
            indices[src], indices[dest] = (
                indices[dest], indices[src])

        urlparts[3] = "".join(
            hash_[index] for index in indices
        ) + urlparts[3][32:]
        return urllib.parse.urlunparse(
            parsed._replace(path="/".join(urlparts)))

    def _extract_video_urls(self, page):
        """Extract video links from a listing page"""
        find = text.re(
            r'href="(https://viralxxxporn\.com'
            r'/video/\d+/[^"]+)"'
        ).findall
        seen = set()
        urls = []
        for url in find(page):
            if url not in seen:
                seen.add(url)
                urls.append(url)
        return urls

    def _extract_album_urls(self, page):
        """Extract album links from a listing page"""
        find = text.re(
            r'href="(https://viralxxxporn\.com'
            r'/album/\d+/[^"]+)"'
        ).findall
        seen = set()
        urls = []
        for url in find(page):
            if url not in seen:
                seen.add(url)
                urls.append(url)
        return urls

    def _pagination(
            self, url, block_id, extract_fn, extractor_cls):
        """KVS AJAX pagination"""
        page_num = 1
        data = {"_extractor": extractor_cls}

        while True:
            if page_num == 1:
                page = self.request(url).text
            else:
                params = {
                    "mode": "async",
                    "function": "get_block",
                    "block_id": block_id,
                    "sort_by": "post_date",
                    "from": page_num,
                }
                response = self.request(
                    url, params=params, expected=(404,))
                if response.status_code == 404:
                    return
                page = response.text

            urls = extract_fn(page)
            if not urls:
                return

            for item_url in urls:
                yield Message.Queue, item_url, data

            page_num += 1


class ViralxxxpornVideoExtractor(ViralxxxpornExtractor):
    """Extractor for individual videos on viralxxxporn.com"""
    subcategory = "video"
    directory_fmt = ("{category}",)
    filename_fmt = "{id}_{title[:80]}.{extension}"
    archive_fmt = "{id}"
    pattern = BASE_PATTERN + r"/video/(\d+)/([^/?#]+)"
    example = "https://viralxxxporn.com/video/12345/title-here/"

    def items(self):
        video_id, slug = self.groups
        url = f"{self.root}/video/{video_id}/{slug}/"
        page = self.request(url, notfound="video").text

        flashvars = text.extr(
            page, "var flashvars", "kt_player(")
        if not flashvars:
            self.log.error("Could not find flashvars")
            return

        video_url = text.extr(
            flashvars, "video_url: '", "'")
        license_code = text.extr(
            flashvars, "license_code: '", "'")

        if not video_url or not license_code:
            self.log.error(
                "Could not extract video URL or license code")
            return

        real_url = self._kvs_get_real_url(
            video_url, license_code)

        title = text.extr(
            flashvars, "video_title: '", "'") or slug
        categories = text.extr(
            flashvars, "video_categories: '", "'") or ""
        tags = text.extr(
            flashvars, "video_tags: '", "'") or ""

        data = {
            "id": text.parse_int(video_id),
            "title": title,
            "slug": slug,
            "categories": (
                categories.split(", ") if categories else []),
            "tags": tags.split(", ") if tags else [],
        }

        yield Message.Directory, "", data
        yield Message.Url, real_url, text.nameext_from_url(
            real_url, data)


class ViralxxxpornAlbumExtractor(ViralxxxpornExtractor):
    """Extractor for photo albums on viralxxxporn.com"""
    subcategory = "album"
    directory_fmt = ("{category}", "{album_id} {title}")
    filename_fmt = "{num:>03}.{extension}"
    archive_fmt = "{album_id}_{num}"
    pattern = BASE_PATTERN + r"/album/(\d+)/([^/?#]+)"
    example = "https://viralxxxporn.com/album/12345/title-here/"

    def items(self):
        album_id, slug = self.groups
        url = f"{self.root}/album/{album_id}/{slug}/"
        page = self.request(url, notfound="album").text

        title = text.unescape(text.extr(
            page, "<h1>", "<") or slug)

        urls = list(text.extract_iter(
            page, '<a href="' + self.root + '/get_image/',
            '"'))
        urls = [
            f"{self.root}/get_image/{u}" for u in urls]

        data = {
            "album_id": text.parse_int(album_id),
            "title": title,
            "slug": slug,
            "count": len(urls),
        }

        yield Message.Directory, "", data
        for data["num"], url in enumerate(urls, 1):
            yield Message.Url, url, text.nameext_from_url(
                url, data)


class ViralxxxpornModelExtractor(ViralxxxpornExtractor):
    """Extractor for model/performer pages on viralxxxporn.com"""
    subcategory = "model"
    pattern = BASE_PATTERN + r"/models/([^/?#]+)"
    example = "https://viralxxxporn.com/models/peachyprime/"

    def items(self):
        model = self.groups[0]
        url = f"{self.root}/models/{model}/"
        block_id = "list_videos_common_videos_list"
        yield from self._pagination(
            url, block_id,
            self._extract_video_urls,
            ViralxxxpornVideoExtractor)


class ViralxxxpornCategoryExtractor(ViralxxxpornExtractor):
    """Extractor for category listing pages on viralxxxporn.com"""
    subcategory = "category"
    pattern = (BASE_PATTERN +
               r"/(latest-updates|shorts)"
               r"(?:/(\d+))?/?$")
    example = "https://viralxxxporn.com/latest-updates/"

    def items(self):
        path = self.groups[0]
        url = f"{self.root}/{path}/"
        if path == "latest-updates":
            block_id = "list_videos_latest_videos_list"
        else:
            block_id = "list_videos_common_videos_list"
        yield from self._pagination(
            url, block_id,
            self._extract_video_urls,
            ViralxxxpornVideoExtractor)


class ViralxxxpornAlbumsExtractor(ViralxxxpornExtractor):
    """Extractor for the albums listing page on viralxxxporn.com"""
    subcategory = "albums"
    pattern = BASE_PATTERN + r"/albums/?$"
    example = "https://viralxxxporn.com/albums/"

    def items(self):
        url = f"{self.root}/albums/"
        block_id = "list_albums_common_albums_list"
        yield from self._pagination(
            url, block_id,
            self._extract_album_urls,
            ViralxxxpornAlbumExtractor)
