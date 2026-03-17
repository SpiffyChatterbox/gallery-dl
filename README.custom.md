# gallery-dl custom branch

Personal fork of [mikf/gallery-dl](https://github.com/mikf/gallery-dl) with
additional extractors and modifications.

## Custom Extractors

| Extractor | Site | Type | FlareSolverr |
|-----------|------|------|:------------:|
| bestthots | https://bestthots.com/ | Gallery | |
| camwhores | https://www.camwhores.video/ | Video | |
| fapfolder | https://fapfolder.club/ | Gallery | Yes |
| feetplaza | https://www.feetplaza.com/ | Gallery | Yes |
| keep2share | https://k2s.cc/ | File hosting | |
| nudogram | https://nudogram.com/ | Gallery | |
| nudostar | https://nudostar.tv/ | Gallery | |
| onlybestgals | https://www.onlybestgals.com/ | Gallery | Yes |
| porn7 | https://porn7.net/ | Video | |
| porndig | https://www.porndig.com/ | Video/Gallery | |
| topfapgirlspics | https://www.topfapgirlspics.com/ | Gallery | Yes |
| viralxxxporn | https://viralxxxporn.com/ | Video/Gallery | |
| youpic | https://youpic.com/ | Photography | |

## Modified Upstream Extractors

| Extractor | Change |
|-----------|--------|
| xvideos | Added `XvideosModelExtractor` for `/models/` and `/pornstars/` URLs |
| nudostar | Refactored with explicit pagination and thumbnail conversion |

## Other Additions

| File | Description |
|------|-------------|
| `gallery_dl/extractor/common.py` | `FlareSolverrMixin` for Cloudflare-protected sites |
| `scripts/rotate-gallery-dl.py` | Utility script |

## FlareSolverr

Extractors marked with **FlareSolverr** require a running
[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) instance to
bypass Cloudflare protection. Configure per-site:

```json
{
    "extractor": {
        "feetplaza": {
            "flaresolverr": "http://localhost:8191"
        }
    }
}
```

## Branching

| Branch | Purpose |
|--------|---------|
| `master` | Tracks upstream mikf/gallery-dl |
| `custom` | All custom extractors and modifications |

New extractor work is done on `custom`. To sync with upstream:

```
git checkout master && git pull upstream master
git checkout custom && git merge master
```
