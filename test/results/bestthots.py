# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import bestthots


__tests__ = (
{
    "#url"     : "https://bestthots.com/aleahjasmine/8338883",
    "#class"   : bestthots.BestthotsPostExtractor,
    "#results" : "https://bestthots.com/storage/images/38052/8338883/5c4dfdb72aba30f4a62e16bdf84d70b7.jpg",
},

{
    "#url"     : "https://bestthots.com/aleahjasmine",
    "#comment" : "Model page with pagination",
    "#class"   : bestthots.BestthotsModelExtractor,
    "#pattern" : r"https://bestthots\.com/storage/images/\d+/\d+/\w+\.jpg",
    "#range"   : "1-50",
    "#count"   : 50,
},

)
