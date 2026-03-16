# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import camwhores


__tests__ = (
{
    "#url"     : "https://www.camwhores.video/videos/16439291/clarkandmartha-onlyfans-anal-virginity-sextape/",
    "#class"   : camwhores.CamwhoresVideoExtractor,
    "#pattern" : r"https://www\.camwhores\.video/get_file/\d+/[a-f0-9]+\w*/\d+/\d+/\d+\.mp4/",
},

{
    "#url"     : "https://www.camwhores.video/search/clarkandmartha/",
    "#class"   : camwhores.CamwhoresSearchExtractor,
    "#pattern" : r"https://www\.camwhores\.video/videos/\d+/[\w-]+/",
    "#count"   : range(10, 80),
},

{
    "#url"     : "https://www.camwhores.video/latest-updates/",
    "#class"   : camwhores.CamwhoresCategoryExtractor,
},

{
    "#url"     : "https://www.camwhores.video/tags/anal/",
    "#class"   : camwhores.CamwhoresCategoryExtractor,
},

)
