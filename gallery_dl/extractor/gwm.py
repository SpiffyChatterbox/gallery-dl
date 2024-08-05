# -*- coding: utf-8 -*-

""" Extractors for Girls with Muscle - www.girlswithmuscle.com """

from .common import Extractor, Message, GalleryExtractor
from .. import text


BASE_PATTERN = (r"(?:https?://)(?:www\.)?girlswithmuscle\.(?:com)")


class GirlsWithMuscleGalleryExtractor(GalleryExtractor):
    """Extractor for catbox albums"""
    category = "gwm"
    subcategory = "album"
    pattern = BASE_PATTERN + r"/images/\?name=[\w\s%]*"
    filename_fmt = "{filename}.{extension}" # Not sure if this is used?
    directory_fmt = ("{category}", "{album_name} ({album_id})") # Not sure if this is used?
    archive_fmt = "{album_id}_{filename}" # Not sure if this is used?


    def metadata(self, page):
        extr = text.extract_from(page)
        self.log.debug(f"Collecting Metadata with {extr}")
        return {
            "album_id"    : self.gallery_url.rpartition("/")[2],
            "album_name" : text.unescape(extr('<h1 id="name-header">', '<')),
            "date"       : text.parse_datetime(extr(
                "<p>Created ", "<"), "%B %d %Y"),
            "description": text.unescape(extr("<p>", "<")),            
        }


    def images(self, page):
        self.log.debug(f"Implementing Image request with {page}")
        return [
            (f"https://www.girlswithmuscle.com/images/{imageid}/", None)    
            for imageid in text.extract_iter(
                    page, '<img class="thumbnail" src="https://www.girlswithmuscle.com/images/thumbs/', '.jpg')
        ]


class _GirlsWithMuscleExtractor(Extractor):
    """Extractor for GirlsWithMuscle Images"""
    category = "gwm"
    directory_fmt = ("{category}", "{user_id}")
    filename_fmt = "{filename}.{extension}"
    pattern = BASE_PATTERN + r"/(?P<imageid>(\d{3,7}))/"

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.user_id = str(match.group(1))


    def items(self):
        host = text.root_from_url(self.url)
        imageURL = host + "/images/full/" + self.user_id + ".jpg"
        url = text.ensure_http_scheme(self.url)
        data = text.nameext_from_url(url, {"url": url})
        extension = text.ext_from_url(imageURL)
        data["extension"] = extension
        filename = self.user_id
        data["filename"] = filename
        user_id = self.user_id
        data["user_id"] = user_id
        
        self.log.debug(f"Sending request to Message with {data}")
        
        yield Message.Directory, data
        yield Message.Url, imageURL, data

