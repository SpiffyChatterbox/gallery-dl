# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.camwhores.video/"""

import urllib.parse
from .common import Extractor, Message
from .. import text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?camwhores\.video"


class CamwhoresExtractor(Extractor):
    """Base class for camwhores extractors"""
    category = "camwhores"
    root = "https://www.camwhores.video"
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
        """Extract non-private video links from a listing page"""
        prefix = self.root + "/videos/"
        urls = []
        seen = set()

        for item in text.extract_iter(
                page, '<div class="item', '</div>'):
            if 'private' in item[:20]:
                continue
            path = text.extr(item, prefix, '"')
            if path and path not in seen:
                seen.add(path)
                urls.append(prefix + path)

        return urls

    def _pagination(self, url, block_id):
        """KVS AJAX pagination"""
        page_num = 1
        data = {"_extractor": CamwhoresVideoExtractor}

        while True:
            if page_num == 1:
                page = self.request(url).text
            else:
                sep = "&" if "?" in url else "?"
                ajax_url = (
                    f"{url}{sep}mode=async"
                    f"&function=get_block"
                    f"&block_id={block_id}"
                    f"&from_videos={page_num}"
                )
                response = self.request(
                    ajax_url, expected=(404,))
                if response.status_code == 404:
                    return
                page = response.text

            video_urls = self._extract_video_urls(page)
            if not video_urls:
                return

            for video_url in video_urls:
                yield Message.Queue, video_url, data

            page_num += 1


class CamwhoresVideoExtractor(CamwhoresExtractor):
    """Extractor for individual videos on camwhores.video"""
    subcategory = "video"
    directory_fmt = ("{category}",)
    filename_fmt = "{id}_{title[:80]}.{extension}"
    archive_fmt = "{id}"
    pattern = BASE_PATTERN + r"/videos/(\d+)/([^/?#]+)"
    example = "https://www.camwhores.video/videos/12345/title-here/"

    def items(self):
        video_id, slug = self.groups
        url = f"{self.root}/videos/{video_id}/{slug}/"
        page = self.request(url, notfound="video").text

        if "This video is a private video" in page:
            self.log.warning("Video %s is private", video_id)
            return

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


class CamwhoresSearchExtractor(CamwhoresExtractor):
    """Extractor for camwhores.video search results"""
    subcategory = "search"
    pattern = BASE_PATTERN + r"/search/([^/?#]+)"
    example = "https://www.camwhores.video/search/QUERY/"

    def items(self):
        url = f"{self.root}/search/{self.groups[0]}/"
        block_id = "list_videos_videos_list_search_result"
        yield from self._pagination(url, block_id)


class CamwhoresCategoryExtractor(CamwhoresExtractor):
    """Extractor for camwhores.video category listing pages"""
    subcategory = "category"
    pattern = (BASE_PATTERN +
               r"/(latest-updates|top-rated|most-popular" +
               r"|categories/[^/?#]+|tags/[^/?#]+)" +
               r"(?:/(\d+))?/?$")
    example = "https://www.camwhores.video/latest-updates/"

    def items(self):
        path = self.groups[0]
        url = f"{self.root}/{path}/"
        if path == "latest-updates":
            block_id = "list_videos_latest_videos_list"
        else:
            block_id = "list_videos_common_videos_list"
        yield from self._pagination(url, block_id)
