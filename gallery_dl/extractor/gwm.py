# -*- coding: utf-8 -*-

""" Extractors for Girls with Muscle - www.girlswithmuscle.com """

from .common import Extractor, Message, GalleryExtractor
from .. import text


BASE_PATTERN = (r"(?:https?://)(?:www\.)?girlswithmuscle\.(?:com)")




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

