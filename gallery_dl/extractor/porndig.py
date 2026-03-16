# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.porndig.com/"""

from .common import Extractor, Message
from .. import text, util

BASE_PATTERN = r"(?:https?://)?(?:www\.)?porndig\.com"


class PorndigExtractor(Extractor):
    """Base class for porndig extractors"""
    category = "porndig"
    root = "https://www.porndig.com"
    request_interval = (1.0, 2.0)

    def _init(self):
        self.cookies.set("dsclcnst", "1", domain=".porndig.com")


class PorndigVideoExtractor(PorndigExtractor):
    """Extractor for individual videos on porndig.com"""
    subcategory = "video"
    directory_fmt = ("{category}",)
    filename_fmt = "{id}_{title[:80]}.{extension}"
    archive_fmt = "{id}"
    pattern = BASE_PATTERN + r"/videos/(\d+)/([^/?#]+)\.html"
    example = "https://www.porndig.com/videos/12345/title-here.html"

    def __init__(self, match):
        PorndigExtractor.__init__(self, match)
        self.video_id = match.group(1)
        self.slug = match.group(2)

    def items(self):
        url = f"{self.root}/videos/{self.video_id}/{self.slug}.html"
        page = self.request(url).text

        # Extract JSON-LD structured data
        json_ld = text.extr(
            page, '<script type="application/ld+json">', '</script>')
        if json_ld:
            data = util.json_loads(json_ld)
        else:
            data = {}

        # Parse the embed URL to get the player video ID
        embed_url = data.get("embedUrl", "")
        # Format: https://videos.porndig.com/player/index/366051/1035/13800
        player_video_id = embed_url.split("/")[-3] if embed_url else None

        # Parse duration from ISO 8601 format (PT19M46S)
        duration_str = data.get("duration", "")
        duration = self._parse_duration(duration_str)

        info = {
            "id": text.parse_int(self.video_id),
            "player_id": text.parse_int(player_video_id),
            "title": data.get("name", ""),
            "description": data.get("description", ""),
            "duration": duration,
            "date": self.parse_datetime_iso(data.get("uploadDate", "")),
            "thumbnail": data.get("thumbnailUrl", ""),
            "tags": (data.get("keywords", "").split(",")
                     if data.get("keywords") else []),
        }

        # Get video sources from player iframe
        if embed_url:
            video_url, quality = self._get_video_url(embed_url)
            if video_url:
                info["quality"] = quality
                yield Message.Directory, "", info
                yield Message.Url, video_url, text.nameext_from_url(
                    video_url, info)
                return

        # Fallback: try to find preview clip
        preview_url = text.extr(page, 'previewclips/', '"')
        if preview_url:
            preview_url = "https://image-cdn.porndig.com/previewclips/" + \
                preview_url
            yield Message.Directory, "", info
            yield Message.Url, preview_url, text.nameext_from_url(
                preview_url, info)

    def _get_video_url(self, embed_url):
        """Fetch the player page and extract video source URLs"""
        try:
            page = self.request(embed_url).text
        except Exception:
            return None, None

        # Extract player_args JSON from the page
        # Format: window.player_args.push({...});
        json_str = text.extr(page, 'window.player_args.push(', ');\n')
        if not json_str:
            return None, None

        try:
            player_data = util.json_loads(json_str)
        except Exception:
            return None, None

        # Look for multi-progressive sources with srcSet
        best_url = None
        best_height = 0

        for source in player_data.get("src", []):
            if source.get("type") == "multi-progressive":
                for item in source.get("srcSet", []):
                    label = item.get("label", "")
                    # Label format: "2160p", "1080p", etc.
                    height = text.parse_int(label.rstrip("p"))
                    if height > best_height:
                        best_height = height
                        best_url = item.get("src")

        if best_url:
            return best_url, f"{best_height}p"

        # Fallback to DASH manifest
        for source in player_data.get("src", []):
            if source.get("type") == "application/dash+xml":
                return source.get("src"), "dash"

        return None, None

    @staticmethod
    def _parse_duration(duration_str):
        """Parse ISO 8601 duration (PT19M46S) to seconds"""
        if not duration_str or not duration_str.startswith("PT"):
            return 0
        duration_str = duration_str[2:]  # Remove PT
        total = 0
        num = ""
        for char in duration_str:
            if char.isdigit():
                num += char
            elif char == "H":
                total += int(num) * 3600
                num = ""
            elif char == "M":
                total += int(num) * 60
                num = ""
            elif char == "S":
                total += int(num)
                num = ""
        return total


class PorndigChannelExtractor(PorndigExtractor):
    """Extractor for porndig channel pages"""
    subcategory = "channel"
    pattern = BASE_PATTERN + r"/channels/(\d+)/([^/?#]+)"
    example = "https://www.porndig.com/channels/41/mature"

    def __init__(self, match):
        PorndigExtractor.__init__(self, match)
        self.channel_id = match.group(1)
        self.channel_name = match.group(2)

    def items(self):
        page_num = 1
        data = {"_extractor": PorndigVideoExtractor}

        while True:
            url = (f"{self.root}/channels/{self.channel_id}/"
                   f"{self.channel_name}?page={page_num}")
            page = self.request(url).text

            # Extract video URLs from the page (deduplicate)
            video_paths = set()
            for video_path in text.extract_iter(
                    page, 'href="/videos/', '"'):
                if video_path.endswith(".html"):
                    video_paths.add(video_path)

            if not video_paths:
                return

            for video_path in sorted(video_paths):
                yield Message.Queue, self.root + "/videos/" + video_path, data

            page_num += 1


class PorndigModelExtractor(PorndigExtractor):
    """Extractor for porndig leaked/model pages"""
    subcategory = "model"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{id}.{extension}"
    archive_fmt = "{model}_{id}"
    pattern = BASE_PATTERN + r"/leaked/([^/?#]+)/?$"
    example = "https://www.porndig.com/leaked/model-name/"

    def __init__(self, match):
        PorndigExtractor.__init__(self, match)
        self.model_name = match.group(1)

    def items(self):
        page_num = 1
        data = {"_extractor": PorndigImageExtractor}

        while True:
            if page_num == 1:
                url = f"{self.root}/leaked/{self.model_name}/"
            else:
                url = f"{self.root}/leaked/{self.model_name}/?page={page_num}"

            page = self.request(url).text

            # Extract image page URLs
            image_urls = list(text.extract_iter(
                page, f'href="/leaked/{self.model_name}/', '"'))

            if not image_urls:
                return

            found_new = False
            for image_path in image_urls:
                # Filter to only numeric IDs (image pages)
                image_id = image_path.rstrip("/")
                if image_id.isdigit():
                    found_new = True
                    yield Message.Queue, \
                        f"{self.root}/leaked/{self.model_name}/{image_id}", \
                        data

            if not found_new:
                return

            page_num += 1


class PorndigImageExtractor(PorndigExtractor):
    """Extractor for individual images on porndig.com leaked pages"""
    subcategory = "image"
    directory_fmt = ("{category}", "{model}")
    filename_fmt = "{model}_{id}.{extension}"
    archive_fmt = "{model}_{id}"
    pattern = BASE_PATTERN + r"/leaked/([^/?#]+)/(\d+)"
    example = "https://www.porndig.com/leaked/model-name/12345"

    def __init__(self, match):
        PorndigExtractor.__init__(self, match)
        self.model_name = match.group(1)
        self.image_id = match.group(2)

    def items(self):
        url = f"{self.root}/leaked/{self.model_name}/{self.image_id}"
        page = self.request(url).text

        # Find the full-size image URL for this specific image ID
        # Pattern: src="https://celebrities-small.../model_id.jpg"
        # Look for src= to get the actual image (not background/thumbnail)
        image_url = None
        search_pattern = f"_{self.image_id}.jpg"

        for img_url in text.extract_iter(
                page, 'src="https://celebrities-small.porndig.com/', '"'):
            full_url = "https://celebrities-small.porndig.com/" + img_url
            # Match by image ID and exclude thumbnails (_300.jpg)
            if search_pattern in full_url and "_300.jpg" not in full_url:
                image_url = full_url
                break

        if not image_url:
            return

        data = {
            "id": text.parse_int(self.image_id),
            "model": self.model_name,
        }

        yield Message.Directory, "", data
        yield Message.Url, image_url, text.nameext_from_url(image_url, data)
