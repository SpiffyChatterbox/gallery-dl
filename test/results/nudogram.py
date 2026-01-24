# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import nudogram


__tests__ = (
{
    "#url"     : "https://nudogram.com/models/ekaterina-naturally/",
    "#category": ("", "nudogram", "model"),
    "#class"   : nudogram.NudogramModelExtractor,
    "#pattern" : r"https://nudogram\.com/contents/e/k/ekaterina-naturally"
                 r"/1000/ekaterina-naturally_\d{4}\.jpg",
    "#count"   : range(350, 450),

    "gallery_id" : "ekaterina-naturally",
    "model_slug" : "ekaterina-naturally",
    "model"      : "Ekaterina_Naturally",
},

{
    "#url"     : "https://nudogram.com/models/ekaterina-naturally/397/",
    "#category": ("", "nudogram", "image"),
    "#class"   : nudogram.NudogramImageExtractor,
    "#pattern" : r"https://nudogram\.com/contents/e/k/ekaterina-naturally"
                 r"/1000/ekaterina-naturally_0397\.jpg",

    "gallery_id" : "ekaterina-naturally",
    "model_slug" : "ekaterina-naturally",
    "model"      : "Ekaterina_Naturally",
    "num"        : 397,
},

)
