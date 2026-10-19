#!/usr/bin/env python3
"""Build index.html for the open web version (GitHub Pages) from the app page.

src/app.html is the same page that runs as the claude.ai artifact. It is an HTML fragment
(claude.ai adds the document skeleton) and loads its fonts from Google. For the open web
version this script wraps it in a full document, swaps Google Fonts for the self-hosted
files in fonts/ (no requests to Google servers) and adds the tags for "add to home screen".

Usage: python3 tools/build_index.py [src/app.html] [index.html]
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "src" / "app.html"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "index.html"

DESCRIPTION = "3x3 Basketball in Berlin: Turniere, Open Gyms und News an einem Ort. Jeden Morgen gecheckt."

RANGES = {
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
             "U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
    "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,"
                 "U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF",
}
FONTS = [
    ("Barlow Condensed", "barlow-condensed", [(700, "normal"), (800, "normal"), (800, "italic")], ["latin", "latin-ext"]),
    ("Figtree", "figtree", [(400, "normal"), (500, "normal"), (600, "normal"), (700, "normal")], ["latin", "latin-ext"]),
    ("JetBrains Mono", "jetbrains-mono", [(400, "normal"), (500, "normal")], ["latin"]),
]


def font_css():
    rules = []
    for family, slug, styles, subsets in FONTS:
        for weight, style in styles:
            for subset in subsets:
                name = f"{slug}-{subset}-{weight}-{style}.woff2"
                if not (ROOT / "fonts" / name).exists():
                    sys.exit(f"Schrift fehlt: fonts/{name}")
                rules.append(
                    f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};font-display:swap;"
                    f"src:url(fonts/{name}) format('woff2');unicode-range:{RANGES[subset]}}}"
                )
    return "\n".join(rules)


def main():
    html = SRC.read_text(encoding="utf-8")
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = m.group(1).strip() if m else "Checkball Berlin"
    html = re.sub(r"<title>.*?</title>\s*", "", html, count=1, flags=re.S)
    html = re.sub(r'<meta name="claude:[^"]*"[^>]*>\s*', "", html)
    html = re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>\s*', "", html)
    html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]*">\s*', "", html)

    m = re.search(r"<style>.*?</style>", html, re.S)
    if not m:
        sys.exit("Kein <style>-Block in der App gefunden")
    style = m.group(0)
    body = (html[: m.start()] + html[m.end():]).strip()
    for host in ("fonts.googleapis.com", "fonts.gstatic.com"):
        if host in body or host in style:
            sys.exit(f"Die App verweist noch auf {host}")

    head = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{DESCRIPTION}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#EEF0F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#101317" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/favicon.svg" type="image/svg+xml">
<link rel="icon" href="icons/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Checkball">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{DESCRIPTION}">
<style>
{font_css()}
</style>
{style}
</head>
<body>
"""
    OUT.write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT} geschrieben ({OUT.stat().st_size // 1024} KB)")

    # Impressum and Datenschutz must be complete before the site is shared publicly.
    for page in ("impressum.html", "datenschutz.html"):
        path = ROOT / page
        if not path.exists():
            print(f"ACHTUNG: {page} fehlt")
        elif "data-todo" in path.read_text(encoding="utf-8"):
            print(f"ACHTUNG: {page} enthält noch Platzhalter (data-todo)")


if __name__ == "__main__":
    main()
