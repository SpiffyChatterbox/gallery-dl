# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from gallery_dl.extractor import fapfolder

__tests__ = (
{
    "#url"     : "https://fapfolder.club/photos/123456",
    "#category": ("", "fapfolder", "photo"),
    "#class"   : fapfolder.FapfolderPhotoExtractor,
},

{
    "#url"     : "https://fapfolder.club/groups/performer",
    "#category": ("", "fapfolder", "group"),
    "#class"   : fapfolder.FapfolderGroupExtractor,
},

{
    "#url"     : "https://fapfolder.club/groups/performer/photos",
    "#category": ("", "fapfolder", "group"),
    "#class"   : fapfolder.FapfolderGroupExtractor,
},

{
    "#url"     : "https://fapfolder.club/username",
    "#category": ("", "fapfolder", "user"),
    "#class"   : fapfolder.FapfolderUserExtractor,
},
)
