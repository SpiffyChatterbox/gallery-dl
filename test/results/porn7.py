# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import porn7


__tests__ = (
{
    "#url"     : "https://porn7.net/post/just-shorts-2725337",
    "#category": ("", "porn7", "post"),
    "#class"   : porn7.Porn7PostExtractor,
    "#pattern" : r"https://cdn\d*\.porn7\.net/uploads\d*/images/.+\.jpg",

    "id"   : 2725337,
    "slug" : "just-shorts",
    "title": str,
},

{
    "#url"     : "https://porn7.net/category/breasts",
    "#category": ("", "porn7", "category"),
    "#class"   : porn7.Porn7CategoryExtractor,
    "#pattern" : porn7.Porn7PostExtractor.pattern,
    "#range"   : "1-20",
    "#count"   : 20,
},

{
    "#url"     : "https://porn7.net/search?q=blonde",
    "#category": ("", "porn7", "search"),
    "#class"   : porn7.Porn7SearchExtractor,
    "#pattern" : porn7.Porn7PostExtractor.pattern,
    "#range"   : "1-20",
    "#count"   : 20,
},

)
