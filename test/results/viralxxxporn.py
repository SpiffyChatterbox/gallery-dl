# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import viralxxxporn


__tests__ = (
{
    "#url"     : "https://viralxxxporn.com/video/359756/peachyprime-sets-the-boat-rocking-with-bigbootybailey-in-a-wild-foursome-video-leak/",
    "#class"   : viralxxxporn.ViralxxxpornVideoExtractor,
    "#pattern" : r"https://viralxxxporn\.com/get_file/\d+/\w+/\d+/359756/359756\.mp4/",
},

{
    "#url"     : "https://viralxxxporn.com/models/peachyprime/",
    "#class"   : viralxxxporn.ViralxxxpornModelExtractor,
    "#pattern" : viralxxxporn.ViralxxxpornVideoExtractor.pattern,
    "#count"   : range(50, 100),
},

{
    "#url"     : "https://viralxxxporn.com/album/17514/atardecer-con-michelle-wick/",
    "#class"   : viralxxxporn.ViralxxxpornAlbumExtractor,
    "#count"   : 71,
},

{
    "#url"     : "https://viralxxxporn.com/latest-updates/",
    "#class"   : viralxxxporn.ViralxxxpornCategoryExtractor,
},

{
    "#url"     : "https://viralxxxporn.com/shorts/",
    "#class"   : viralxxxporn.ViralxxxpornCategoryExtractor,
},

{
    "#url"     : "https://viralxxxporn.com/albums/",
    "#class"   : viralxxxporn.ViralxxxpornAlbumsExtractor,
},

)
