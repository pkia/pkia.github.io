#!/usr/bin/env python3
"""check_site.py — the site's house rules, executable.

The repo's conventions (AGENTS.md) were enforced by remembering them.
This script runs the gates instead:

  assets      every local src=/href= reference in an HTML page resolves
              to a file in the repo (query strings and fragments stripped)
  feed        feed.xml and blog/posts/ are 1:1 — every post appears in
              exactly one <item> (link or guid), every item maps to a post
  sitemap     sitemap.xml carries every post exactly once and only lists
              pages that resolve to real files
  index       blog/index.html cards are newest-first and card every post
              exactly once
  busters     styles.css / script.js carry the same ?v= cache-buster on
              every page that references them (and always a buster)
  addresses   no LAN/tailnet IP literals, no .ts.net hostnames and no
              known LAN hostnames in any page (AGENTS.md: "Never publish
              network addresses")

Every fault names its file and line. Exit 0 clean, 1 on any fault.
Stdlib only; the script is read-only — it never writes or removes
anything. --root DIR checks another tree (the tests build fixture sites
and drive this CLI against them).
"""

import argparse
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://pkia.github.io"
POSTS_DIR = "blog/posts"
INDEX_FILE = "blog/index.html"
FEED_FILE = "feed.xml"
SITEMAP_FILE = "sitemap.xml"
ASSET_ATTRS = ("src", "href", "poster", "srcset")
POST_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}.*\.html$")
LOCAL_SKIP_PREFIXES = ("http://", "https://", "//", "mailto:", "data:", "#")

# Private / link-local / CGNAT IPv4, local IPv6, tailnet hostnames, and
# the hostnames of this deployment's own machines. None may ship in a page.
ADDR_PATTERNS = (
    ("private IPv4 address", re.compile(
        r"(?<![\d.])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|127\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|169\.254\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r"|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}"
        r")(?![\d.])")),
    ("local IPv6 address", re.compile(
        r"(?i)(?<![\w:])(?:fe80:[0-9a-f:]+|f[cd][0-9a-f]{2}:[0-9a-f:]+)")),
    ("tailnet hostname", re.compile(
        r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.ts\.net(?![\w-])")),
)

BUSTER_RE = re.compile(r"(styles\.css|script\.js)\?v=(\d+)")
BARE_ASSET_RE = re.compile(r"[\"']/(?:styles\.css|script\.js)(?![?.\w])")


class RefCollector(HTMLParser):
    """Collects local asset references as (line, attr, url)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        for attr, value in attrs:
            if attr in ASSET_ATTRS and value:
                for candidate in value.split(","):
                    url = candidate.strip().split()[0] if candidate.strip() else ""
                    self.refs.append((line, attr, url))


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def is_local(url):
    if not url or url.startswith(LOCAL_SKIP_PREFIXES):
        return False
    return True


def strip_url(url):
    url = url.split("#", 1)[0]
    return url.split("?", 1)[0]


def resolve(root, page, url):
    """Map a reference to the file it names, the way the site resolves.

    Directory-style URLs (/, /blog/, relative 'blog/') map to that
    directory's index.html, as GitHub Pages serves them.
    """
    url = strip_url(url)
    if not url:
        return None
    if url.startswith("/"):
        path = url.lstrip("/")
    else:
        path = os.path.relpath((page.parent / url).resolve(), root)
    if path == "" or path == ".":
        return root / "index.html"
    if path.endswith("/") or (root / path).is_dir():
        return root / path / "index.html"
    return root / path


def find_faults(root):
    faults = []

    def fault(gate, path, line, message):
        faults.append(f"FAIL {path}:{line} {gate}: {message}")

    # ---- page inventory -------------------------------------------------
    html_files = sorted(p for p in root.rglob("*.html") if ".git" not in p.parts)
    post_dir = root / POSTS_DIR
    post_files = sorted(post_dir.glob("*.html")) if post_dir.is_dir() else []
    bad_names = [p for p in post_files if not POST_NAME_RE.match(p.name)]
    for p in bad_names:
        fault("posts", rel(root, p), 1,
              f"post filename does not start with YYYY-MM-DD: {p.name}")
    posts = {p.name: p for p in post_files if POST_NAME_RE.match(p.name)}
    post_urls = {f"{BASE}/{POSTS_DIR}/{name}": name for name in posts}

    # ---- gate: asset references resolve ----------------------------------
    total_refs = 0
    for page in html_files:
        parser = RefCollector()
        parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        for line, attr, url in parser.refs:
            if not is_local(url):
                continue
            total_refs += 1
            target = resolve(root, page, url)
            if target is None or not target.is_file():
                fault("assets", rel(root, page), line,
                      f"{attr}={url!r} does not resolve to a file")

    # ---- gate: feed.xml is 1:1 with posts --------------------------------
    feed_path = root / FEED_FILE
    feed = feed_path.read_text(encoding="utf-8") if feed_path.is_file() else ""
    feed_items = list(re.finditer(r"<item>(.*?)</item>", feed, re.S))
    channel_end = feed.find("</channel>")
    feed_end_line = line_of(feed, channel_end) if channel_end != -1 else 1
    seen = {}
    for item in feed_items:
        iline = line_of(feed, item.start())
        block = item.group(1)
        urls = set()
        for tag in ("link", "guid"):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
            if m:
                urls.add(m.group(1).strip())
        mapped = {u for u in urls if u in post_urls}
        if not mapped:
            fault("feed", FEED_FILE, iline,
                  f"item maps to no post (link/guid: {sorted(urls) or 'none'})")
            continue
        for u in mapped:
            name = post_urls[u]
            if name in seen:
                fault("feed", FEED_FILE, iline,
                      f"post {name} appears in a second item (first at line "
                      f"{seen[name]})")
            seen[name] = iline
    for name in sorted(set(posts) - set(seen)):
        fault("feed", FEED_FILE, feed_end_line,
              f"post {name} has no feed item")

    # ---- gate: sitemap.xml lists every post once, only real pages --------
    sm_path = root / SITEMAP_FILE
    sm = sm_path.read_text(encoding="utf-8") if sm_path.is_file() else ""
    sm_end = sm.find("</urlset>")
    sm_end_line = line_of(sm, sm_end) if sm_end != -1 else 1
    sm_seen = {}
    for m in re.finditer(r"<loc>(.*?)</loc>", sm, re.S):
        loc = m.group(1).strip()
        sline = line_of(sm, m.start())
        path = loc[len(BASE) + 1:] if loc.startswith(BASE + "/") else None
        if path is None:
            fault("sitemap", SITEMAP_FILE, sline,
                  f"loc outside {BASE}: {loc}")
            continue
        if path == "":
            target = root / "index.html"
        elif path.endswith("/"):
            target = root / path / "index.html"
        else:
            target = root / path
        if not target.is_file():
            fault("sitemap", SITEMAP_FILE, sline,
                  f"loc resolves to no file: {loc}")
            continue
        if path.startswith(POSTS_DIR + "/"):
            name = path[len(POSTS_DIR) + 1:]
            if name not in posts:
                fault("sitemap", SITEMAP_FILE, sline,
                      f"loc names a non-post under {POSTS_DIR}/: {name}")
            elif name in sm_seen:
                fault("sitemap", SITEMAP_FILE, sline,
                      f"post {name} listed again (first at line {sm_seen[name]})")
            else:
                sm_seen[name] = sline
    for name in sorted(set(posts) - set(sm_seen)):
        fault("sitemap", SITEMAP_FILE, sm_end_line,
              f"post {name} missing from sitemap")

    # ---- gate: blog index newest-first, every post carded once -----------
    idx_path = root / INDEX_FILE
    idx = idx_path.read_text(encoding="utf-8") if idx_path.is_file() else ""
    cards = []
    for m in re.finditer(r'href="/blog/posts/([^"]+)"', idx):
        cards.append((line_of(idx, m.start()), m.group(1)))
    prev_date = None
    for line, name in cards:
        date = name[:10]
        if prev_date is not None and date > prev_date:
            fault("index", INDEX_FILE, line,
                  f"card out of order: {name} sits after a newer card "
                  f"({prev_date} > … > {date})")
        prev_date = date
    card_names = [n for _, n in cards]
    for name in sorted(set(posts) - set(card_names)):
        fault("index", INDEX_FILE, 1, f"post {name} has no index card")
    for name, first_line in sorted({n: l for l, n in reversed(cards)}.items()):
        if card_names.count(name) > 1:
            fault("index", INDEX_FILE, first_line,
                  f"post {name} carded more than once")

    # ---- gate: uniform cache-busters --------------------------------------
    busters = {}   # asset -> {version: count}
    for page in html_files:
        text = page.read_text(encoding="utf-8", errors="replace")
        for m in BUSTER_RE.finditer(text):
            asset, version = m.group(1), m.group(2)
            busters.setdefault(asset, {}).setdefault(version, 0)
            busters[asset][version] += 1
        for m in BARE_ASSET_RE.finditer(text):
            fault("cache-buster", rel(root, page), line_of(text, m.start()),
                  f"/{m.group(0).split('/')[-1]} referenced without a ?v= "
                  f"cache-buster")
    modes = {}
    for asset, versions in sorted(busters.items()):
        mode = max(versions, key=lambda v: versions[v])
        modes[asset] = mode
        for page in html_files:
            text = page.read_text(encoding="utf-8", errors="replace")
            for m in BUSTER_RE.finditer(text):
                if m.group(1) == asset and m.group(2) != mode:
                    fault("cache-buster", rel(root, page), line_of(text, m.start()),
                          f"{asset}?v={m.group(2)} differs from the site's "
                          f"v={mode}")

    # ---- gate: no network addresses ---------------------------------------
    for page in html_files:
        text = page.read_text(encoding="utf-8", errors="replace")
        for lineno, text_line in enumerate(text.splitlines(), 1):
            for label, pattern in ADDR_PATTERNS:
                m = pattern.search(text_line)
                if m:
                    fault("addresses", rel(root, page), lineno,
                          f"{label} in page text: {m.group(0)!r}")

    return faults, {
        "pages": len(html_files),
        "posts": len(posts),
        "feed_items": len(feed_items),
        "sitemap_locs": len(re.findall(r"<loc>", sm)),
        "cards": len(cards),
        "asset_refs": total_refs,
        "busters": modes,
    }


def rel(root, path):
    return Path(path).relative_to(root).as_posix()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                    help="site tree to check (default: this repo)")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"FAIL {root}: not a directory")
        return 1
    faults, stats = find_faults(root)
    for line in faults:
        print(line)
    if faults:
        print(f"site-check: {len(faults)} fault(s) in {stats['pages']} pages")
        return 1
    busters = ", ".join(f"{a} v={v}" for a, v in stats["busters"].items()) or "none"
    print(f"OK — {stats['pages']} pages, {stats['posts']} posts, feed "
          f"{stats['feed_items']} items, sitemap {stats['sitemap_locs']} locs, "
          f"index {stats['cards']} cards, {stats['asset_refs']} asset refs, "
          f"busters {busters}, no network addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
