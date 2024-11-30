# -*- coding: utf-8 -*-
from .common import Extractor, Message, GalleryExtractor
from .. import text
import re

BASE_PATTERN = r"(?:https?://)?thotporn\.tv"

# Gallery: https://thotporn.tv/hazey_haley


class ThotpornGalleryExtractor(GalleryExtractor):
    """Extractor for Thotporn Galleries"""
    category = "thotporn"
    directory_fmt = ("{category}", "{user_id}")
    filename_fmt = "{user_id}_{filename}.{extension}"
    pattern = BASE_PATTERN + r"/([^&#]+)*$"
    # sampleurl = "https://thotporn.tv/hazey_haley"
    # Todo: Come back and get /video/

    def __init__(self, match):
        self.root = text.root_from_url(match.group(0))
        self.gallery_url = match.group(0)
        self.user_id = match.groups(0)[0]
        print(f'Storing user_id as {self.user_id}')
        GalleryExtractor.__init__(self, match, self.gallery_url)

    def images(self, page):
        """Return a list of all (image-url, metadata)-tuples"""
        urllist = []
        page_number = 2  # Start with page 2 for API requests
        print(f"Beginning page 1:")
        # First process the initial HTML page
        for container in text.extract_iter(page, 'class="light-gallery-item"',
                                           '>'):
            # Skip JavaScript template strings
            if "'+src+'" in container or "'+title+'" in container:
                continue

            image_url = text.extract(container, 'data-src="', '"')[0]
            if not image_url:
                continue

            image_id = text.extract(container, 'data-title="', '"')[0]
            if not image_id:
                continue

            metadata = {
                "filename": f"{self.user_id}_{image_id}",
                "user_id": self.user_id
            }
            print(f"Found image: {image_url}")
            urllist.append((image_url, metadata))

        print("Done with page 1")

        # Then start making API requests for subsequent pages
        while True:
            # Get JSON response for current page
            url = f"{self.gallery_url}?page={page_number}&type=all"
            print(f"Beginning page {page_number}: {url}")

            try:
                response = self.request(
                    url,
                    headers={"X-Requested-With": "XMLHttpRequest"}
                )
                print(
                    f"Response content type: {response.headers.get('content-type', 'unknown')}")
                print(f"Response content preview: {response.text[:200]}")

                json_data = response.json()

                # Check if we've reached the end (empty array)
                if not json_data:
                    print(
                        f"Received empty response on page {page_number} - ending pagination")
                    break

                # Process each image in the JSON response
                for item in json_data:
                    image_url = item.get('player')
                    if not image_url:
                        continue

                    image_id = item.get('id')
                    if not image_id:
                        continue

                    metadata = {
                        "filename": f"{self.user_id}_{image_id}",
                        "user_id": self.user_id,
                        "date": item.get('published_date')
                    }

                    urllist.append((image_url, metadata))
                    print(f"Found image: {image_url}")

                print(f"Found {len(json_data)} images on page {page_number}")

                page_number += 1

            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
                break

        print(f"Total URLs collected: {len(urllist)}")
        return urllist

    def metadata(self, page):
        """Return metadata dictionary"""
        return {
            "gallery_id": self.user_id,
            "title": self.user_id,
            "user_id": self.user_id,
        }


class ThotpornExtractor(Extractor):
    """Extractor for Thotporn Images"""
    category = "thotporn"
    directory_fmt = ("{category}", "{user_id}")
    filename_fmt = "{filename}.{extension}"
    pattern = BASE_PATTERN + r"/([^&#/]+)*/photo/(\d*)"
    # sampleurl = "https://thotporn.tv/hazey_haley/photo/5487299"
    # Todo: Come back and get /video/

    def __init__(self, match):
        Extractor.__init__(self, match)
        self.user_id, self.image_id = match.groups()

    def items(self):
        """Return a list of all (image-url, metadata)-tuples"""
        pagetext = self.request(self.url, notfound=self.subcategory).text
        divdata = text.extract(pagetext, '<div class="actor-detail-image">', '</div>')
        print(f"extracting initial data: {divdata}")
        img_url = text.extract(divdata[0], 'src=\"', '\"')
        img_url = img_url[0]
        print(f"Extracting Image URL: {img_url}")

        data = text.nameext_from_url(img_url, {"url": img_url})
        data["filename"] = self.user_id + '-' + self.image_id
        data["user_id"] = self.user_id
        print(f"preparing data string: {data}")

        yield Message.Directory, data
        yield Message.Url, img_url, data
