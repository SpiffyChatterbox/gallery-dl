# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import topfapgirlspics

__tests__ = (
{
    "#url"     : "https://www.topfapgirlspics.com/tisha-alyn/t/28918959023391/",
    "#category": ("", "topfapgirlspics", "photo"),
    "#class"   : topfapgirlspics.TopfapgirlspicsPhotoExtractor,
},

{
    "#url"     : "https://www.topfapgirlspics.com/tisha-alyn-o9URj/",
    "#category": ("", "topfapgirlspics", "model"),
    "#class"   : topfapgirlspics.TopfapgirlspicsModelExtractor,
},

{
    "#url"     : "https://www.topfapgirlspics.com/new/",
    "#category": ("", "topfapgirlspics", "category"),
    "#class"   : topfapgirlspics.TopfapgirlspicsCategoryExtractor,
},

{
    "#url"     : "https://www.topfapgirlspics.com/random/",
    "#category": ("", "topfapgirlspics", "category"),
    "#class"   : topfapgirlspics.TopfapgirlspicsCategoryExtractor,
},

{
    "#url"     : "https://www.topfapgirlspics.com/new/2/",
    "#category": ("", "topfapgirlspics", "category"),
    "#class"   : topfapgirlspics.TopfapgirlspicsCategoryExtractor,
},
)
