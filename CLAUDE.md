# Claude Code: Gallery-dl Extractor Development Guide

This document provides instructions for Claude Code when developing new extractors for gallery-dl.

## Project Overview

**Project:** gallery-dl - Command-line program to download image galleries from various websites
**Repository:** https://github.com/SpiffyChatterbox/gallery-dl (personal fork)
**Upstream:** https://github.com/mikf/gallery-dl
**Language:** Python 3

---

## Git Configuration & Branching Strategy

### Branching Model

This is a **personal fork** maintained independently from upstream. We use a two-branch model:

| Branch | Purpose |
|--------|---------|
| `master` | Synced with upstream mikf/gallery-dl |
| `custom` | Our custom extractors and modifications |

### Workflow

1. **Keep `master` synced with upstream:**
   ```bash
   git checkout master
   git pull upstream master
   git push origin master
   ```

2. **Work on the `custom` branch:**
   ```bash
   git checkout custom
   # Make changes, commit
   ```

3. **Periodically merge upstream changes into custom:**
   ```bash
   git checkout custom
   git merge master
   # Resolve any conflicts
   ```

### Remotes

```bash
origin    git@github.com:SpiffyChatterbox/gallery-dl.git (our fork)
upstream  https://github.com/mikf/gallery-dl.git (mikf's repo)
```

### Push Commands

**IMPORTANT: Always use the SpiffyChatterbox SSH key for git operations.**

```bash
# Push to origin
GIT_SSH_COMMAND="ssh -i ~/.ssh/spiffychatterbox_ed25519" git push origin custom

# Push master after syncing with upstream
GIT_SSH_COMMAND="ssh -i ~/.ssh/spiffychatterbox_ed25519" git push origin master
```

**Never use other accounts for this repository.**

---

## Custom Extractors

Our custom extractors (on the `custom` branch):

| Extractor | Description |
|-----------|-------------|
| fapfolder | Gallery extractor |
| feetplaza | Foot fetish gallery site (uses FlareSolverr) |
| onlybestgals | Gallery extractor |
| porn7 | Video extractor |
| topfapgirlspics | Gallery extractor |
| youpic | Photographer portfolio extractor |

### FlareSolverr Mixin

We have a custom `FlareSolverrMixin` in `common.py` for sites with Cloudflare protection:

```python
from .common import Extractor, FlareSolverrMixin, Message

class MySiteExtractor(FlareSolverrMixin, Extractor):
    """Extractor that uses FlareSolverr for Cloudflare bypass"""
    category = "mysite"
    root = "https://mysite.com"
```

Configure in `gallery-dl.conf`:
```json
{
  "extractor": {
    "mysite": {
      "flaresolverr": "http://localhost:8191"
    }
  }
}
```

---

## Development Workflow for New Extractors

### Phase 1: Site Research (CRITICAL - Do First!)

Before writing any code, thoroughly research the target site:

#### 1.1 URL Structure Analysis
- Visit the site and collect example URLs for all content types
- Identify patterns:
  - Individual items (photos, videos, posts)
  - Collections (galleries, albums, sets)
  - User/creator pages
  - Tag/category pages
  - Search results

#### 1.2 Technical Investigation
```bash
# Test for API endpoints
curl "https://site.com/page.json"
curl "https://site.com/api/posts"

# Check Network tab in DevTools:
# - Look for AJAX/API calls
# - Check JSON responses
# - Note pagination methods
# - Identify authentication requirements
```

#### 1.3 HTML Structure Analysis
If the user saves an HTML page:
- Use `Grep` tool to find image patterns
- Look for: `data-image`, `src=`, photo URLs, pagination
- Note: Watch for "view-source" format (Firefox) which HTML-encodes content

#### 1.4 Find Similar Extractors
```bash
cd gallery-dl/gallery_dl/extractor

# Search by site characteristics:
grep -l "GalleryExtractor" *.py    # Gallery/album sites
grep -l "BooruExtractor" *.py      # Tag-based imageboards
grep -l "oauth" *.py               # OAuth authentication
grep -l "pagination" *.py          # Pagination patterns
```

**Decision Matrix:**
| Site Has | Base Class | Study These |
|----------|------------|-------------|
| Tag-based posts, JSON API | `BooruExtractor` | danbooru, gelbooru |
| Galleries/albums | `GalleryExtractor` | imgur, deviantart |
| Social media feed | `Extractor` | twitter, tumblr |
| Creator platforms | `Extractor` | patreon, fanbox |
| XenForo forums | `Extractor` | xenforo (formerly simpcity) |
| Cloudflare protected | `FlareSolverrMixin` | feetplaza |

---

### Phase 2: Implementation

#### 2.1 Create Base Extractor Class

**Always create a base class for shared properties:**

```python
class SiteNameExtractor(Extractor):
    """Base class for sitename extractors"""
    category = "sitename"
    root = "https://sitename.com"
```

**Benefits:**
- DRY principle (Don't Repeat Yourself)
- Single source of truth for `category` and `root`
- Easy to add shared methods later
- Follows gallery-dl patterns

#### 2.2 Implement Specific Extractors

**For each content type, inherit from base class:**

```python
class SiteNamePhotoExtractor(SiteNameExtractor):
    """Extractor for individual photos"""
    subcategory = "photo"
    directory_fmt = ("{category}", "{user}")
    filename_fmt = "{user}_{id}.{extension}"
    archive_fmt = "{id}"
    pattern = BASE_PATTERN + r"/photos/(\d+)"
    example = "https://sitename.com/photos/12345"

    def __init__(self, match):
        SiteNameExtractor.__init__(self, match)
        self.photo_id = match.group(1)

    def items(self):
        # Extract data from HTML/API
        url = f"{self.root}/photos/{self.photo_id}"
        page = self.request(url).text

        # Parse metadata
        image_url = text.extr(page, 'data-image="', '"')
        user = text.extr(page, 'data-user="', '"')

        data = {
            "id": text.parse_int(self.photo_id),
            "user": user,
        }

        yield Message.Directory, "", data
        yield Message.Url, image_url, text.nameext_from_url(image_url, data)
```

#### 2.3 Key Patterns

**Use utility functions (never reinvent):**
```python
from .. import text, exception

# String extraction
text.extr(page, 'start', 'end')
text.extract_iter(page, 'start', 'end')

# Type conversions
text.parse_int(string, default=0)
text.parse_timestamp(unix_timestamp)

# URL handling
text.nameext_from_url(url, data)
text.urljoin(base, relative)
```

**Queue other extractors:**
```python
# For galleries that contain multiple photos
for photo_url in photo_urls:
    yield Message.Queue, photo_url, {"_extractor": PhotoExtractor}
```

**Error handling:**
```python
if not data:
    raise exception.NotFoundError("photo")
```

---

### Phase 3: Code Quality

#### 3.1 Style Checks
```bash
python -m flake8 gallery_dl/extractor/sitename.py
```

**Common issues:**
- Lines > 79 characters (split across multiple lines)
- Missing blank lines
- Incorrect indentation

#### 3.2 Registration

Add to `gallery_dl/extractor/__init__.py` in alphabetical order:
```python
modules = [
    ...
    "existingsite",
    "sitename",        # Add here
    "nextsite",
    ...
]
```

#### 3.3 Verification
```bash
# Verify extractor is registered
python -m gallery_dl --list-extractors | grep sitename

# Test URL pattern matching (without downloading)
python -m gallery_dl -g "https://sitename.com/..."
```

#### 3.4 Test Cases

Add test cases to `test/results/sitename.py`:
```python
from gallery_dl.extractor import sitename

__tests__ = (
{
    "#url"     : "https://sitename.com/gallery/example/",
    "#category": ("", "sitename", "gallery"),
    "#class"   : sitename.SiteNameGalleryExtractor,
    "#pattern" : r"https://sitename\.com/uploads/.+\.jpg",
    "#count"   : range(10, 20),

    "gallery_id": 12345,
    "title"     : "Example Gallery",
},
)
```

---

### Phase 4: Handling Cloudflare Protection

If the site uses Cloudflare protection (403/challenge errors):

#### Solution 1: FlareSolverr Mixin (Our Custom Solution)
```python
from .common import Extractor, FlareSolverrMixin, Message

class MySiteExtractor(FlareSolverrMixin, Extractor):
    category = "mysite"
    root = "https://mysite.com"
```

Configure in `gallery-dl.conf`:
```json
{
  "extractor": {
    "mysite": {
      "flaresolverr": "http://localhost:8191"
    }
  }
}
```

#### Solution 2: Browser Cookies
```bash
python -m gallery_dl \
  --cookies-from-browser firefox:/path/to/firefox/profile \
  "https://site.com/..."
```

**Find Firefox profile:**
```bash
# Linux/Snap
ls ~/.mozilla/firefox/
ls ~/snap/firefox/common/.mozilla/firefox/

# Windows
%APPDATA%\Mozilla\Firefox\Profiles\

# macOS
~/Library/Application Support/Firefox/Profiles/
```

#### Solution 3: Configuration File

Update `/media/veracrypt1/etc/gallery-dl.conf`:
```json
{
  "extractor": {
    "sitename": {
      "cookies": {
        "cf_clearance": "..."
      }
    }
  }
}
```

#### Solution 4: Manual Cookie Export
- Use browser extension to export cookies.txt
- Load with `--cookies cookies.txt`

---

## Best Practices Checklist

Before considering an extractor complete:

### Research Phase
- [ ] Analyzed all URL patterns (photos, galleries, users, tags)
- [ ] Checked for public API endpoints
- [ ] Tested pagination methods
- [ ] Identified authentication requirements
- [ ] Found 2-3 similar extractors to study
- [ ] Determined correct base class to use

### Implementation Phase
- [ ] Created base extractor class with shared properties
- [ ] All extractors inherit from base class
- [ ] Used `text.*` utility functions (not manual parsing)
- [ ] Used `self.request()` (not `requests.get()`)
- [ ] Proper error handling with `exception.NotFoundError`
- [ ] All metadata extracted (id, user, title, date, tags, etc.)
- [ ] Supports all major content types for the site

### Code Quality Phase
- [ ] Passed flake8 with zero errors
- [ ] Lines <= 79 characters
- [ ] Followed PEP 8 naming conventions
- [ ] Used f-strings (not old % or .format())
- [ ] Removed unnecessary constructors
- [ ] Added to `__init__.py` in correct alphabetical position
- [ ] Extractor appears in `--list-extractors`
- [ ] Added test cases to `test/results/`

### Testing Phase
- [ ] Tested with real URLs
- [ ] Handled Cloudflare/rate limiting
- [ ] Verified file downloads work
- [ ] Checked edge cases (empty galleries, missing data)
- [ ] Tested multiple page templates if site has variations

---

## Common Mistakes to Avoid

### Don't Override Base Class Methods Unnecessarily
```python
# WRONG - GalleryExtractor already has items()
class MyGallery(GalleryExtractor):
    def items(self):
        # Custom implementation
```

### Don't Manually Parse Strings
```python
# WRONG
title = page.split('<title>')[1].split('</title>')[0]

# RIGHT
title = text.extr(page, '<title>', '</title>')
```

### Don't Duplicate Class Variables
```python
# WRONG - Repeated in every class
class SitePhoto(Extractor):
    category = "site"
    root = "https://site.com"

class SiteGallery(Extractor):
    category = "site"
    root = "https://site.com"

# RIGHT - Use base class
class SiteExtractor(Extractor):
    category = "site"
    root = "https://site.com"

class SitePhoto(SiteExtractor):
    subcategory = "photo"
```

### Don't Forget Message.Directory Format
```python
# WRONG - Missing empty string
yield Message.Directory, data

# RIGHT - Include empty string as second argument
yield Message.Directory, "", data
```

---

## Reference Documentation

### Essential Files to Read
1. `/media/veracrypt1/gallery-dl-framework-guide.md` - Comprehensive extractor development guide
2. `gallery_dl/extractor/common.py` - Base Extractor classes
3. `gallery_dl/extractor/booru.py` - BooruExtractor base class
4. Similar site extractor - Your template

### External Resources
- **Wiki:** https://github.com/mikf/gallery-dl/wiki/Developing-Extractors
- **Discussions:** Issue #1656, #6489 on GitHub
- **Config Docs:** https://github.com/mikf/gallery-dl/blob/master/docs/configuration.rst

---

## Troubleshooting

### "HttpError: MissingSchema: Invalid URL"
**Cause:** `self.root` not defined
**Fix:** Add `root = "https://site.com"` to base class

### "ChallengeError: Cloudflare challenge (403)"
**Cause:** Cloudflare protection
**Fix:** Use FlareSolverr mixin or `--cookies-from-browser` with browser cookies

### "No matches found" when grepping HTML
**Cause:** HTML file is in "view-source" format (Firefox)
**Fix:** Save page with Ctrl+S (not view source), or parse the escaped HTML

### Flake8 "line too long"
**Cause:** Lines > 79 characters
**Fix:** Split across multiple lines:
```python
# WRONG (85 characters)
yield Message.Queue, photo_url, {"_extractor": FapfolderPhotoExtractor}

# RIGHT
yield Message.Queue, photo_url, {
    "_extractor": FapfolderPhotoExtractor}
```

### "ValueError - not enough values to unpack"
**Cause:** Message tuple has wrong number of elements
**Fix:** Ensure `Message.Directory` has 3 elements: `yield Message.Directory, "", data`

---

## Environment Setup

### User Configuration
- **Firefox Profile:** `/home/ahallberg/snap/firefox/common/.mozilla/firefox/844v2x2z.default`
- **Gallery-dl Config:** `/media/veracrypt1/etc/gallery-dl.conf`
- **Gallery-dl Repo:** `/media/veracrypt1/dev/gallery-dl/`
- **Working Directory:** `/media/veracrypt1/`

### SSH Keys
- **SpiffyChatterbox (USE THIS):** `~/.ssh/spiffychatterbox_ed25519`
- **gymzombie (DO NOT USE):** `~/.ssh/gymzombie_ed25519`

### Testing Commands
```bash
# Development
cd /media/veracrypt1/dev/gallery-dl

# Style check
python -m flake8 gallery_dl/extractor/sitename.py

# List extractors
python -m gallery_dl --list-extractors | grep sitename

# Test extraction (URLs only, no download)
python -m gallery_dl -g "https://site.com/gallery/example/"

# Test with cookies
python -m gallery_dl \
  -c /media/veracrypt1/etc/gallery-dl.conf \
  --cookies-from-browser firefox:/home/ahallberg/snap/firefox/common/.mozilla/firefox/844v2x2z.default \
  -g "https://site.com/gallery/example/"
```

---

## Key Insights

1. **Research before coding** - Spend time studying the site and similar extractors
2. **Use base classes** - Create a base extractor for shared properties (category, root)
3. **Follow the framework** - 80% of code should come from base classes, you only add site-specific logic
4. **Study similar sites** - Don't reinvent patterns that already exist
5. **Cloudflare is common** - Use FlareSolverr mixin or browser cookies
6. **Use utility functions** - text.extr(), text.parse_int(), etc. - don't parse manually
7. **Handle template variations** - Sites often have different templates for old vs new content
8. **Sync regularly** - Keep master synced with upstream to get bug fixes and new features

---

## Success Criteria

An extractor is complete when:

- All major content types supported (photos, galleries, users, videos, etc.)
- Passes flake8 with zero errors
- Uses base class for shared properties
- Follows gallery-dl coding patterns
- Extracts comprehensive metadata
- Handles edge cases gracefully
- Works with real URLs (with proper authentication if needed)
- Has test cases in `test/results/`
- Committed to the `custom` branch
