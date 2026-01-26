# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://k2s.cc/ (Keep2Share)"""

import time
from .common import Extractor, Message
from .. import text, exception

BASE_PATTERN = r"(?:https?://)?(?:www\.)?(k2s|keep2share)\.cc"


class Keep2shareExtractor(Extractor):
    """Base class for Keep2Share extractors"""
    category = "keep2share"
    root = "https://k2s.cc"
    root_api = "https://keep2share.cc/api/v2"

    def _init(self):
        self.api = Keep2shareAPI(self)


class Keep2shareFileExtractor(Keep2shareExtractor):
    """Extractor for Keep2Share file downloads"""
    subcategory = "file"
    archive_fmt = "{file_id}"
    filename_fmt = "{filename}.{extension}"
    directory_fmt = ("{category}",)
    pattern = BASE_PATTERN + r"/file/([0-9a-f]+)(?:/([^/?#]+))?"
    example = "https://k2s.cc/file/abc123def/filename.mp4"

    def __init__(self, match):
        Keep2shareExtractor.__init__(self, match)
        self.file_id = match.group(2)
        self.url_filename = match.group(3)

    def items(self):
        file_info = self.api.get_file_status(self.file_id)

        if not file_info.get("is_available"):
            raise exception.NotFoundError("file")

        data = {
            "file_id": self.file_id,
            "filename": file_info.get("name", ""),
            "filesize": file_info.get("size", 0),
            "access": file_info.get("access", ""),
        }

        # Extract video info if available
        video_info = file_info.get("video_info")
        if video_info:
            data["duration"] = video_info.get("duration")
            data["width"] = video_info.get("width")
            data["height"] = video_info.get("height")
            data["video_format"] = video_info.get("format")

        text.nameext_from_url(data["filename"], data)

        # Get download URL
        download_url = self.api.get_url(self.file_id)

        yield Message.Directory, "", data
        yield Message.Url, download_url, data


class Keep2shareAPI:
    """Interface for the Keep2Share API"""

    def __init__(self, extractor):
        self.extractor = extractor
        self.root = extractor.root_api
        self.log = extractor.log
        self.auth_token = None
        self.captcha_mode = extractor.config("captcha")

        # Authenticate if credentials are provided
        username = extractor.config("username")
        password = extractor.config("password")
        if username and password:
            self.auth_token = self._login(username, password)

    def _login(self, username, password):
        """Login to get auth_token"""
        self.log.info("Logging in as %s", username)
        data = {
            "username": username,
            "password": password,
        }
        result = self._call("login", data)
        if result.get("status") == "success":
            self.log.info("Login successful")
            return result.get("auth_token")
        else:
            self.log.warning("Login failed: %s", result.get("message"))
            return None

    def get_file_status(self, file_id):
        """Get file information"""
        data = {"id": file_id}
        return self._call("getFileStatus", data)

    def request_captcha(self):
        """Request a captcha challenge from the API"""
        result = self._call("requestCaptcha", {})
        if result.get("status") == "success":
            return {
                "challenge": result.get("challenge"),
                "captcha_url": result.get("captcha_url"),
            }
        return None

    def get_url(self, file_id):
        """Get download URL for a file"""
        data = {"file_id": file_id}

        if self.auth_token:
            # Premium download with authentication
            data["auth_token"] = self.auth_token
        else:
            # Free slow download - pass null captcha params
            data["free_download_key"] = None
            data["captcha_challenge"] = None
            data["captcha_response"] = None

        result = self._call("getUrl", data)
        self.log.debug("getUrl response: %s", result)

        if result.get("status") == "success":
            url = result.get("url")

            # Check if we got a download URL or need to wait
            if url:
                self.log.debug("Download URL: %s", url)
                if not self.auth_token:
                    self.log.info("Using free slow download (speed limited)")
                return url

            # No URL yet - need to wait for free download slot
            free_key = result.get("free_download_key")
            time_wait = result.get("time_wait", 0)

            if free_key and time_wait:
                return self._wait_for_download(file_id, free_key, time_wait)

            # Unexpected response
            self.log.error("Unexpected API response: %s", result)
            raise exception.StopExtraction("No download URL in response")

        error_code = result.get("errorCode")
        message = result.get("message", "Unknown error")

        if error_code == 20:
            raise exception.NotFoundError("file")
        elif error_code in (30, 31):
            # Captcha required - try manual solving if enabled
            if self.captcha_mode == "manual":
                return self._solve_captcha_manual(file_id)
            raise exception.AuthenticationError(
                "Captcha required (free download rate limit reached). "
                "Use 'captcha': 'manual' or provide premium credentials."
            )
        elif error_code == 10:
            raise exception.AuthenticationError(
                "Authentication required. Please provide credentials."
            )
        else:
            raise exception.StopExtraction(
                "API error %s: %s", error_code, message
            )

    def _wait_for_download(self, file_id, free_key, time_wait):
        """Wait for free download slot and get URL"""
        minutes = time_wait // 60
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            wait_str = f"{hours}h {mins}m"
        else:
            wait_str = f"{mins}m"

        self.log.warning("Free download queue: %s wait time", wait_str)

        # Check max wait time config (default: 300 seconds = 5 minutes)
        max_wait = self.extractor.config("max-wait", 300)
        if time_wait > max_wait:
            raise exception.StopExtraction(
                "Wait time (%s) exceeds max-wait (%ds). "
                "Use premium account or increase 'max-wait' config.",
                wait_str, max_wait)

        self.log.info("Waiting for download slot...")

        # Wait for the specified time
        time.sleep(time_wait)

        # Request the actual download URL
        data = {
            "file_id": file_id,
            "free_download_key": free_key,
        }

        result = self._call("getUrl", data)
        self.log.debug("getUrl after wait: %s", result)

        if result.get("status") == "success":
            url = result.get("url")
            if url:
                self.log.info("Download slot ready!")
                return url

        message = result.get("message", "Unknown error")
        error_code = result.get("errorCode", "")
        raise exception.StopExtraction(
            "Failed after wait: [%s] %s", error_code, message)

    def _solve_captcha_manual(self, file_id):
        """Prompt user to manually solve captcha"""
        # Request captcha challenge
        captcha_info = self.request_captcha()
        if not captcha_info:
            raise exception.StopExtraction("Failed to request captcha")

        challenge = captcha_info["challenge"]
        captcha_url = captcha_info["captcha_url"]

        # Use HTTPS for the captcha URL
        if captcha_url.startswith("http://"):
            captcha_url = "https://" + captcha_url[7:]

        # Display instructions
        self.log.warning("=" * 60)
        self.log.warning("CAPTCHA REQUIRED")
        self.log.warning("=" * 60)
        self.log.info("Open this image in your browser:")
        self.log.info("   %s", captcha_url)
        self.log.info("")
        self.log.info("Type the text you see in the image below.")
        self.log.warning("=" * 60)

        # Prompt for captcha text
        token = self.extractor.input("\nEnter captcha text (Enter to skip): ")

        if not token or not token.strip():
            raise exception.AuthenticationError(
                "Captcha token required for download")

        token = token.strip()
        self.log.info("Attempting download with captcha token...")

        # Retry with captcha solution
        data = {
            "file_id": file_id,
            "free_download_key": challenge,
            "captcha_challenge": challenge,
            "captcha_response": token,
        }

        result = self._call("getUrl", data)
        self.log.debug("getUrl response: %s", result)

        if result.get("status") == "success":
            self.log.info("Captcha accepted! Starting download...")
            url = result.get("url")
            self.log.debug("Download URL: %s", url)
            return url

        error_code = result.get("errorCode")
        message = result.get("message", "Unknown error")

        if error_code in (30, 31):
            raise exception.AuthenticationError(
                "Invalid captcha token. Please try again.")
        else:
            raise exception.StopExtraction(
                "API error %s: %s", error_code, message)

    def _call(self, endpoint, data):
        """Make an API call"""
        url = f"{self.root}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        response = self.extractor.request(
            url, method="POST", headers=headers, json=data, fatal=False
        )
        return response.json()
