"""tests for tools/check_site.py — the site's house rules, executable.

Every gate is proven by planting its fault into a fixture site and
driving the real CLI; each planted fault must fail naming file and line.
The real repo tree must pass (that test is also the house-rules gate
CI runs).
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "tools" / "check_site.py"
BASE = "https://pkia.github.io"

PAGE_HEAD = (
    "<!DOCTYPE html>\n"
    '<html lang="en">\n<head>\n'
    '  <link rel="stylesheet" href="/styles.css?v={v}" />\n'
    '  <link rel="icon" href="/favicon.svg" />\n'
    '  <script src="/script.js?v={v}" defer></script>\n'
    "</head>\n<body>\n"
)
PAGE_TAIL = "</body>\n</html>\n"


def page(body="hello", v=3):
    return PAGE_HEAD.format(v=v) + body + PAGE_TAIL


def feed_xml(items):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0">', "  <channel>",
             "    <title>EV — Devlog</title>",
             f"    <link>{BASE}/blog/</link>"]
    for name in items:
        url = f"{BASE}/blog/posts/{name}"
        lines += ["    <item>", f"      <title>t</title>",
                  f"      <link>{url}</link>",
                  f'      <guid isPermaLink="true">{url}</guid>',
                  "      <pubDate>Mon, 02 Nov 2026 07:00:00 +0100</pubDate>",
                  "    </item>"]
    lines += ["  </channel>", "</rss>", ""]
    return "\n".join(lines)


def sitemap_xml(names):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset>']
    for path in names:
        lines.append(f"  <url><loc>{BASE}{path}</loc></url>")
    lines += ["</urlset>", ""]
    return "\n".join(lines)


def blog_index(cards):
    lines = ['<!DOCTYPE html>', '<html lang="en">', '<head>',
             '  <link rel="stylesheet" href="/styles.css?v=3" />',
             '</head>', '<body>', '  <div id="post-list">']
    for name in cards:
        lines.append(f'    <article class="post-card"><h2>'
                     f'<a href="/blog/posts/{name}">{name}</a></h2>'
                     f'</article>')
    lines += ["  </div>", "</body>", "</html>", ""]
    return "\n".join(lines)


def make_site(root, posts=("2026-11-02.html", "2026-11-01.html"),
              cards=None, feed=None, sitemap=None):
    """A minimal but fully valid fixture site; defaults are consistent."""
    (root / "blog" / "posts").mkdir(parents=True)
    (root / "styles.css").write_text("body { color: #fff; }\n")
    (root / "script.js").write_text("console.log(1);\n")
    (root / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>\n")
    (root / "index.html").write_text(page("<h1>EV</h1><a href=\"/blog/\">blog</a>"))
    (root / "404.html").write_text(page("<h1>lost</h1>"))
    (root / "blog" / "index.html").write_text(blog_index(cards or posts))
    (root / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n")
    for i, name in enumerate(posts):
        (root / "blog" / "posts" / name).write_text(page(f"<p>post {i}</p>"))
    (root / "feed.xml").write_text(feed_xml(feed or posts))
    (root / "sitemap.xml").write_text(sitemap_xml(
        sitemap or ["/", "/blog/"] + [f"/blog/posts/{p}" for p in posts]))
    return root


def run(root):
    return subprocess.run([sys.executable, str(CHECKER), "--root", str(root)],
                          capture_output=True, text=True, timeout=60)


@pytest.fixture
def site(tmp_path):
    return make_site(tmp_path / "site")


def test_clean_fixture_passes(site):
    r = run(site)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout
    assert "2 posts" in r.stdout
    assert "feed 2 items" in r.stdout
    assert "busters script.js v=3, styles.css v=3" in r.stdout


def test_real_repo_tree_passes():
    r = run(REPO)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout
    assert "no network addresses" in r.stdout


def test_dangling_asset_names_file_and_line(site):
    p = site / "blog" / "posts" / "2026-11-01.html"
    p.write_text(p.read_text() + '  <img src="/missing.png" alt="x" />\n')
    r = run(site)
    assert r.returncode == 1
    line = f"blog/posts/2026-11-01.html:{len(p.read_text().splitlines())}"
    assert f"FAIL {line} assets" in r.stdout
    assert "missing.png" in r.stdout


def test_dangling_relative_asset(site):
    p = site / "blog" / "posts" / "2026-11-02.html"
    p.write_text(p.read_text() + '  <img src="local.png" alt="x" />\n')
    r = run(site)
    assert r.returncode == 1
    assert "assets" in r.stdout and "local.png" in r.stdout


def test_feed_missing_post(site):
    (site / "feed.xml").write_text(feed_xml(["2026-11-02.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "feed.xml" in r.stdout
    assert "2026-11-01.html has no feed item" in r.stdout


def test_feed_item_maps_to_no_post(site):
    (site / "feed.xml").write_text(feed_xml(
        ["2026-11-02.html", "2026-12-31.html", "2026-11-01.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "item maps to no post" in r.stdout
    assert "2026-12-31.html" in r.stdout


def test_feed_duplicate_item(site):
    (site / "feed.xml").write_text(feed_xml(
        ["2026-11-02.html", "2026-11-02.html", "2026-11-01.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "appears in a second item" in r.stdout


def test_sitemap_missing_post(site):
    (site / "sitemap.xml").write_text(sitemap_xml(
        ["/", "/blog/", "/blog/posts/2026-11-02.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "2026-11-01.html missing from sitemap" in r.stdout


def test_sitemap_loc_resolves_to_no_file(site):
    (site / "sitemap.xml").write_text(sitemap_xml(
        ["/", "/blog/", "/nope/", "/blog/posts/2026-11-02.html",
         "/blog/posts/2026-11-01.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "sitemap.xml:5" in r.stdout
    assert "resolves to no file" in r.stdout


def test_sitemap_duplicate_post(site):
    (site / "sitemap.xml").write_text(sitemap_xml(
        ["/", "/blog/", "/blog/posts/2026-11-02.html",
         "/blog/posts/2026-11-02.html", "/blog/posts/2026-11-01.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "listed again" in r.stdout


def test_index_out_of_order_names_offending_line(site):
    (site / "blog" / "index.html").write_text(blog_index(
        ["2026-11-01.html", "2026-11-02.html"]))
    r = run(site)
    assert r.returncode == 1
    # the newer card is the second card: line 9 of blog/index.html
    assert re.search(r"FAIL blog/index\.html:9 index: card out of order",
                     r.stdout)
    assert "2026-11-02.html" in r.stdout


def test_index_missing_card(site):
    (site / "blog" / "index.html").write_text(blog_index(["2026-11-02.html"]))
    r = run(site)
    assert r.returncode == 1
    assert "2026-11-01.html has no index card" in r.stdout


def test_cache_buster_drift(site):
    (site / "index.html").write_text(page("<h1>EV</h1>", v=2))
    r = run(site)
    assert r.returncode == 1
    assert "cache-buster" in r.stdout
    assert "styles.css?v=2 differs from the site's v=3" in r.stdout
    assert "index.html:" in r.stdout


def test_cache_buster_missing(site):
    (site / "index.html").write_text(
        page("<h1>EV</h1>").replace('href="/styles.css?v=3"',
                                    'href="/styles.css"'))
    r = run(site)
    assert r.returncode == 1
    assert "without a ?v= cache-buster" in r.stdout


def test_private_ip_in_post_names_file_and_line(site):
    p = site / "blog" / "posts" / "2026-11-01.html"
    p.write_text(p.read_text() + "  <p>reachable at 192.168.0.25 tonight</p>\n")
    r = run(site)
    assert r.returncode == 1
    assert "addresses" in r.stdout
    assert "192.168.0.25" in r.stdout
    assert re.search(r"FAIL blog/posts/2026-11-01\.html:\d+ addresses", r.stdout)


def test_tailnet_hostname_is_an_address(site):
    p = site / "blog" / "posts" / "2026-11-02.html"
    p.write_text(p.read_text() + "  <p>see switchlab.tailnet.ts.net</p>\n")
    r = run(site)
    assert r.returncode == 1
    assert "tailnet hostname" in r.stdout
    assert "switchlab.tailnet.ts.net" in r.stdout


# ---- addresses gate over published non-HTML text ------------------------
# feed.xml item text, robots.txt, sitemap.xml and the CSS/JS assets are
# all served public; an address can ride in a feed description or a
# robots directive exactly as it can ride in a page.

def _first_item_description(site, description):
    feed_p = site / "feed.xml"
    text = feed_p.read_text().replace(
        "    </item>",
        f"      <description>{description}</description>\n    </item>", 1)
    feed_p.write_text(text)
    lineno = next(i for i, line in enumerate(text.splitlines(), 1)
                  if description in line)
    return lineno


def test_address_in_feed_description_names_file_and_line(site):
    lineno = _first_item_description(
        site, "tonight the worker answered at 192.168.0.25")
    r = run(site)
    assert r.returncode == 1
    assert f"FAIL feed.xml:{lineno} addresses" in r.stdout
    assert "192.168.0.25" in r.stdout


def test_ts_net_hostname_in_feed_description_faults(site):
    _first_item_description(
        site, "read it on switchlab.tailnet.ts.net while it lasted")
    r = run(site)
    assert r.returncode == 1
    assert "FAIL feed.xml:" in r.stdout
    assert "tailnet hostname" in r.stdout
    assert "switchlab.tailnet.ts.net" in r.stdout


def test_address_in_robots_txt_names_file_and_line(site):
    (site / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n"
        "# stage mirror lives at 10.0.0.7\n"
        "Sitemap: https://pkia.github.io/sitemap.xml\n")
    r = run(site)
    assert r.returncode == 1
    assert re.search(r"FAIL robots\.txt:3 addresses", r.stdout)
    assert "10.0.0.7" in r.stdout


def test_address_in_stylesheet_faults(site):
    (site / "styles.css").write_text(
        "body { background: url(http://192.168.0.9/cam.png); }\n")
    r = run(site)
    assert r.returncode == 1
    assert re.search(r"FAIL styles\.css:1 addresses", r.stdout)
    assert "192.168.0.9" in r.stdout


# ---- SVG and JSON are served text too ------------------------------------
# The favicon is an SVG; any manifest or data file would be JSON. SVG
# markup carries text nodes (<desc>, <title>) the same way a feed line
# does, so the scan follows the served-text set, not the HTML set.

def test_address_in_svg_desc_names_file_and_line(site):
    (site / "favicon.svg").write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>\n"
        "  <desc>cluster switch lives at 192.168.0.25</desc>\n"
        "</svg>\n")
    r = run(site)
    assert r.returncode == 1
    assert re.search(r"FAIL favicon\.svg:2 addresses", r.stdout)
    assert "192.168.0.25" in r.stdout


def test_ts_net_hostname_in_svg_faults(site):
    (site / "favicon.svg").write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>\n"
        "  <desc>read it on switchlab.tailnet.ts.net while it lasted</desc>\n"
        "</svg>\n")
    r = run(site)
    assert r.returncode == 1
    assert "tailnet hostname" in r.stdout
    assert "switchlab.tailnet.ts.net" in r.stdout


def test_address_in_json_faults(site):
    (site / "manifest.json").write_text(
        '{\n  "name": "EV",\n'
        '  "debug_endpoint": "http://10.0.0.7:8800"\n}\n')
    r = run(site)
    assert r.returncode == 1
    assert re.search(r"FAIL manifest\.json:3 addresses", r.stdout)
    assert "10.0.0.7" in r.stdout


def test_public_urls_in_svg_and_json_are_not_faults(site):
    # the site's own public origin rides in served SVG/JSON the same way
    # it rides in the feed and robots.txt — never a fault
    (site / "favicon.svg").write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>\n"
        f"  <desc>home is {BASE}/blog/</desc>\n"
        "</svg>\n")
    (site / "manifest.json").write_text(
        f'{{\n  "start_url": "{BASE}/blog/"\n}}\n')
    r = run(site)
    assert r.returncode == 0, r.stdout
    assert "no network addresses" in r.stdout


def test_public_origin_urls_in_published_text_are_not_faults(site):
    # the site's own public-origin URLs ride in feed item text and
    # robots.txt on every real page of this repo — never a fault
    _first_item_description(
        site, "full story at https://pkia.github.io/blog/")
    r = run(site)
    assert r.returncode == 0, r.stdout
    assert "no network addresses" in r.stdout


def test_public_ip_is_not_flagged(site):
    p = site / "blog" / "posts" / "2026-11-01.html"
    p.write_text(p.read_text() + "  <p>example: 93.184.216.34 and "
                 "https://example.com</p>\n")
    r = run(site)
    assert r.returncode == 0, r.stdout


def test_post_filename_without_date_prefix(site):
    (site / "blog" / "posts" / "scratch.html").write_text(page("<p>x</p>"))
    r = run(site)
    assert r.returncode == 1
    assert "does not start with YYYY-MM-DD" in r.stdout


def test_directory_urls_resolve_to_index(site):
    # '/' and '/blog/' hrefs are normal on every page; the fixture uses
    # them and still passes — this only pins the behaviour explicitly.
    assert run(site).returncode == 0


def test_checker_is_read_only():
    src = CHECKER.read_text()
    for banned in ("write_text", "unlink", "os.remove", "shutil", "subprocess",
                   "open("):
        assert banned not in src, f"checker source must not {banned!r}"
