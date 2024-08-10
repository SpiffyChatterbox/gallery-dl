# -*- coding: utf-8 -*-

""" Extractors for Girls with Muscle - www.girlswithmuscle.com """

from .common import Extractor, Message, GalleryExtractor
from .. import text
import re

BASE_PATTERN = r"(?:https?://)(?:www\.)?girlswithmuscle\.(?:com)"

# TODO: get a testfile up and running


class GirlsWithMuscleGalleryExtractor(GalleryExtractor):
    """Extractor for GWM albums"""
    category = "gwm"
    pattern = BASE_PATTERN + r"/images/\?name=([^&#]+)*"
    filename_fmt = "{filename}.{extension}"
    directory_fmt = ("{category}", "{gallery_id}")

    def __init__(self, match):
        self.root = text.root_from_url(match.group(0))
        self.girls_name = match.group(1)
        self.foldername = self.girls_name.replace('%20', '_')
        url = "https://www.girlswithmuscle.com/images/?name=" + self.girls_name
        GalleryExtractor.__init__(self, match, url)

    def metadata(self, page):
        extr = text.extract_from(page)
        return {"gallery_id": self.foldername}
        # TODO: Maybe collect Tags here?

    def images(self, page):
        urllist = []
        url_pattern = re.compile(r"<img class='thumbnail' src='https://www\.girlswithmuscle\.com/images/thumbs/(\d{1,20}).jpg(\?\d)?\b")
        for match in url_pattern.finditer(page):
            imageid = match.group(1)
            videocheck = match.group(2)
            if videocheck:
                urllist.append("https://www.girlswithmuscle.com/images/full/" + imageid + ".mp4")
            else:
                urllist.append("https://www.girlswithmuscle.com/images/full/" + imageid + ".jpg")
        self.log.debug(f"Implementing Image request with {urllist}")
        return [
            (image, None)
            for image in urllist
        ]
        ## TODO: Occasionally finds a .png and that fails because I assume .jpg
        ## TODO: Occasionally the site lists a video as an image and it fails because we ask for the wrong file extension
            # Example: https://www.girlswithmuscle.com/images/?name=Claudia Elizabeth (cdzfit) links to https://www.girlswithmuscle.com/images/thumbs/2276507.jpg, but at view-source:https://www.girlswithmuscle.com/2276507/ we find an mp4.
        ## TODO: Currently only pulls down the first page. How do we iterate through pages?


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


# TODO: Forum threads (https://www.girlswithmuscle.com/forum/)
# TODO: Other "categories" like
#   pinned (hidden gems) (https://www.girlswithmuscle.com/images/?show_only=pinned&order=pinned)
#   high scores (https://www.girlswithmuscle.com/images/?order=scoreday)
#   tags (Is this even queryable?)
#   users (https://www.girlswithmuscle.com/users/userlist/?sort=total_score_received)
