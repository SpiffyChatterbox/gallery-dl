# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import feetplaza

__tests__ = (
{
    "#url"     : "https://www.feetplaza.com/naomi/292412/perfect-feet/",
    "#category": ("", "feetplaza", "post"),
    "#class"   : feetplaza.FeetplazaPostExtractor,
},

{
    "#url"     : "https://www.feetplaza.com/models/naomi/",
    "#category": ("", "feetplaza", "model"),
    "#class"   : feetplaza.FeetplazaModelExtractor,
},

{
    "#url"     : "https://www.feetplaza.com/category/soles/",
    "#category": ("", "feetplaza", "category"),
    "#class"   : feetplaza.FeetplazaCategoryExtractor,
},
)
