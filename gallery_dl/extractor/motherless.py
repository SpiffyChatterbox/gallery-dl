# -*- coding: utf-8 -*-


from .common import Extractor, Message
from .. import text



BASE_PATTERN = r"(?:https?://)?motherless\.com"

class MotherlessExampleExtractor(Extractor):
    category = "motherless"
    subcategory = "test"
    pattern = BASE_PATTERN 

    def items(self):
        url = self.url
        page = self.request(text.ensure_http_scheme(url)).text
        testtext = text.extract(page, '<link rel="image_src" type="image/jpg" href="', '">')
        imgeURL = testtext[0]
        data = text.nameext_from_url(url, {"url": url})
        
        yield Message.Directory, data
        yield Message.Url, imgeURL, data
        
        