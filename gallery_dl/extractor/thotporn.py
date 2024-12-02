# -*- coding: utf-8 -*-
from .common import Extractor, Message, GalleryExtractor
from .. import text
import base64

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

    def decode_video_url(encoded_string):
        """
        Decode an encoded video URL.

        Args:
            encoded_string (str): The encoded URL string, may include additional path components

        Returns:
            str: The fully decoded and assembled URL
        """
        try:
            # Split on comma if there are additional path components
            parts = encoded_string.split(',')
            encoded_base = parts[0]

            # Reverse the string and decode base64
            reversed_string = encoded_base[::-1]  # Python string reversal
            decoded_bytes = base64.b64decode(reversed_string)
            base_url = decoded_bytes.decode('utf-8')

            # If there were additional path components, add them back
            if len(parts) > 1:
                # The second part should be the path components
                path = parts[1]
                # Ensure we have a proper path separator
                if not base_url.endswith('/'):
                    base_url += '/'
                if path.startswith('/'):
                    path = path[1:]
                full_url = base_url + path
            else:
                full_url = base_url

            return full_url

        except Exception as e:
            return f"Error decoding: {str(e)}"

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

            # Check if this is a video item
            video_data = text.extract(container, 'data-video="{', '}"')[0]
            if video_data:
                try:
                    video_id = text.extract(container, 'data-title="', '"')[0]

                    # Get the encoded source
                    encoded_src = text.extract(video_data, '"src":"', '"')[0]
                    if not encoded_src:
                        continue

                    # First make the view increment request
                    view_url = f"{self.root}/view_incr?id={video_id}"
                    print(f"Processing video {video_id}")

                    view_response = self.request(
                        view_url,
                        headers={"X-Requested-With": "XMLHttpRequest"},
                        referer=self.gallery_url
                    ).json()

                    if view_response.get('success'):
                        decoded_url = self.decode_video_url(encoded_src)
                        metadata = {
                            "filename": f"{self.user_id}_{video_id}",
                            "user_id": self.user_id,
                            "extension": None,  # Let youtube-dl determine this
                            "type": "video",
                            "_ytdl": True  # Flag for youtube-dl processing
                        }
                        urllist.append((decoded_url, metadata))
                        print(f"Found video: {video_id}")

                except Exception as e:
                    print(f"Error processing video data: {e}")
                    continue
            else:
                # This is an image item
                image_url = text.extract(container, 'data-src="', '"')[0]
                if not image_url or image_url.startswith('+'):
                    continue

                image_id = text.extract(container, 'data-title="', '"')[0]
                if not image_id or image_id.startswith('+'):
                    continue

                metadata = {
                    "filename": f"{self.user_id}_{image_id}",
                    "user_id": self.user_id,
                    "type": "image"
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
                json_data = response.json()
                # Check if we've reached the end (empty array)
                if not json_data:
                    print(
                        f"Received empty response on page {page_number} - ending pagination")
                    break

                # Process each image in the JSON response
                for item in json_data:
                    # Handle both video and image items from API response
                    if 'video' in item:
                        # Handle video item
                        video_url = item.get('video_url')
                        if not video_url:
                            continue

                        metadata = {
                            "filename": f"{self.user_id}_{item['id']}",
                            "user_id": self.user_id,
                            "extension": "mp4",
                            "type": "video",
                            "date": item.get('published_date')
                        }
                        urllist.append((video_url, metadata))
                        print(f"Found video: {video_url}")

                    else:
                        # Handle image item as before
                        image_url = item.get('player')
                        if not image_url:
                            continue

                        metadata = {
                            "filename": f"{self.user_id}_{item['id']}",
                            "user_id": self.user_id,
                            "type": "image",
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




'''
# Code to pull down the webpage:
import requests
response = requests.get('https://thotporn.tv/skylar_blue')
html_content = response.text
print(html_content)
'''
