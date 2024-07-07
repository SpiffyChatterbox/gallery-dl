# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

gallery_dl = __import__("gallery_dl.extractor.gwm")
_gwm = getattr(gallery_dl.extractor, "gwm")


__tests__ = (
{
    "#url"     : "https://www.girlswithmuscle.com/2293513/",
    "#category": ("gwm"),
    "#sha1_url"    : "5080b9804c713347f01aa349d3fa1abea90faae1",
}
)
