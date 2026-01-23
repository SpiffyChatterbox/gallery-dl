# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import youpic


__tests__ = (
{
    "#url"     : "https://youpic.com/darialytvyn",
    "#category": ("", "youpic", "user"),
    "#class"   : youpic.YoupicUserExtractor,
    "#pattern" : r"https://youpic\.com/y/huge/[0-9a-f]+",
    "#count"   : range(10, 50),
},

{
    "#url"     : "https://youpic.com/photo/1055120330279940",
    "#category": ("", "youpic", "image"),
    "#class"   : youpic.YoupicImageExtractor,
    "#pattern" : r"https://youpic\.com/y/huge/7b3314e28ec1bd4b441c8dcf"
                 r"8133192f405db3d3ffff07000000000036393d00",
    "#count"   : 1,

    "id"       : 1055120330279940,
    "title"    : "Carlo ",
    "width"    : 5107,
    "height"   : 3405,
},

{
    "#url"     : "https://youpic.com/inspiration",
    "#category": ("", "youpic", "inspiration"),
    "#class"   : youpic.YoupicInspirationExtractor,
    "#pattern" : r"https://youpic\.com/y/huge/[0-9a-f]+",
    "#range"   : "1-10",
    "#count"   : 10,
},

{
    "#url"     : "https://youpic.com/newest",
    "#category": ("", "youpic", "newest"),
    "#class"   : youpic.YoupicNewestExtractor,
    "#pattern" : r"https://youpic\.com/y/huge/[0-9a-f]+",
    "#range"   : "1-10",
    "#count"   : 10,
},

)
