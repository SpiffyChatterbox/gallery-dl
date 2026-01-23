# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import onlybestgals

__tests__ = (
{
    "#url"     : "https://www.onlybestgals.com/model/tawny-swain-9t0ky/",
    "#category": ("", "onlybestgals", "model"),
    "#class"   : onlybestgals.OnlybestgalsModelExtractor,
},

{
    "#url"     : "https://www.onlybestgals.com/new-models/",
    "#category": ("", "onlybestgals", "category"),
    "#class"   : onlybestgals.OnlybestgalsCategoryExtractor,
},

{
    "#url"     : "https://www.onlybestgals.com/random/",
    "#category": ("", "onlybestgals", "category"),
    "#class"   : onlybestgals.OnlybestgalsCategoryExtractor,
},

{
    "#url"     : "https://www.onlybestgals.com/new-models/2/",
    "#category": ("", "onlybestgals", "category"),
    "#class"   : onlybestgals.OnlybestgalsCategoryExtractor,
},
)
