#!/usr/bin/env python3
"""Translated pages: which exist, which are behind the English, and the language menus.

English is the source. A translation of `dashboard.mdx` into Spanish lives at `es/dashboard.mdx`.
Only the pages in `i18n/config.json` "pages" are translated; every other page appears in each
language's menu as its English page, so a reader who switches language keeps the whole site.

`i18n/pages.lock.json` records, per language and page, a hash of the English the translation
was made from. When the English changes the translation is "stale": still published, but
behind, until somebody retranslates it and runs `stamp`.

The language menus in docs.json are generated from the English one (the `en` entry under
`navigation.languages`) plus the tab and group names in `i18n/nav.<locale>.json`, so a page
added to the English menu reaches every language with no hand edit.

Commands, run from the repo root:

    python3 scripts/i18n-pages.py status            # per language: missing, stale, current
    python3 scripts/i18n-pages.py nav               # rewrite the language menus in docs.json
    python3 scripts/i18n-pages.py links             # point links in translations at translated pages
    python3 scripts/i18n-pages.py stamp <locale> <page>...   # record a finished translation
    python3 scripts/i18n-pages.py check             # CI: menus current, every listed page exists,
                                                    # no link to the English of a translated page;
                                                    # stale translations are warnings
"""
import hashlib
import json
import os
import re
import sys

CONFIG = json.load(open("i18n/config.json"))
LOCALES = CONFIG["locales"]
PAGES = CONFIG["pages"]
LOCK_PATH = "i18n/pages.lock.json"
SOURCE = "en"

# A link to a site page: Markdown ](/page), ](/page#x), and href="/page" in components.
LINK = re.compile(r'(\]\(|href=")/([a-z0-9/_-]+)((?:#[^)"\s]*)?)(?=[)"])')


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def source_hash(page):
    return hashlib.sha256(read(f"{page}.mdx").encode()).hexdigest()[:16]


def load_lock():
    return json.load(open(LOCK_PATH)) if os.path.exists(LOCK_PATH) else {}


def page_state(locale, page, lock):
    if not os.path.exists(f"{locale}/{page}.mdx"):
        return "missing"
    return "current" if lock.get(locale, {}).get(page) == source_hash(page) else "stale"


def english_nav(config):
    for lang in config["navigation"]["languages"]:
        if lang["language"] == SOURCE:
            return lang
    sys.exit("docs.json has no navigation.languages entry for en")


def localize_pages(pages, locale, names):
    out = []
    for item in pages:
        if isinstance(item, str):
            translated = item in PAGES and os.path.exists(f"{locale}/{item}.mdx")
            out.append(f"{locale}/{item}" if translated else item)
        else:
            group = dict(item)
            group["group"] = names.get(item["group"], item["group"])
            group["pages"] = localize_pages(item["pages"], locale, names)
            out.append(group)
    return out


def build_language(en, locale):
    names_path = f"i18n/nav.{locale}.json"
    names = json.load(open(names_path)) if os.path.exists(names_path) else {}
    lang = {"language": locale}
    tabs = []
    for tab in en["tabs"]:
        t = dict(tab)
        t["tab"] = names.get(tab["tab"], tab["tab"])
        t["groups"] = localize_pages(tab["groups"], locale, names)
        tabs.append(t)
    lang["tabs"] = tabs
    return lang


def built_nav(config):
    en = english_nav(config)
    return [en] + [build_language(en, locale) for locale in LOCALES]


def localize_links(text, locale):
    def swap(m):
        page = m.group(2).rstrip("/")
        if page in PAGES and os.path.exists(f"{locale}/{page}.mdx"):
            return f"{m.group(1)}/{locale}/{page}{m.group(3)}"
        return m.group(0)

    return LINK.sub(swap, text)


def cmd_status():
    lock = load_lock()
    for locale in LOCALES:
        states = {p: page_state(locale, p, lock) for p in PAGES}
        counts = {s: sum(1 for v in states.values() if v == s) for s in ("current", "stale", "missing")}
        behind = [p for p, s in states.items() if s != "current"]
        print(f"{locale:6} {counts['current']}/{len(PAGES)} current, {counts['stale']} stale, {counts['missing']} missing"
              + (f"  ({', '.join(behind)})" if behind else ""))
    return 0


def cmd_nav(check):
    config = json.load(open("docs.json"))
    want = built_nav(config)
    if config["navigation"]["languages"] == want:
        print("i18n: language menus are current")
        return 0
    if check:
        print("::error::docs.json language menus are out of date. Run python3 scripts/i18n-pages.py nav and commit.")
        return 1
    config["navigation"]["languages"] = want
    write("docs.json", json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    print("i18n: rewrote the language menus in docs.json")
    return 0


def cmd_links(check):
    bad = 0
    for locale in LOCALES:
        for page in PAGES:
            path = f"{locale}/{page}.mdx"
            if not os.path.exists(path):
                continue
            text = read(path)
            fixed = localize_links(text, locale)
            if fixed == text:
                continue
            if check:
                print(f"::error file={path}::links to the English of a page that has a {locale} translation. Run python3 scripts/i18n-pages.py links.")
                bad += 1
            else:
                write(path, fixed)
                print(f"i18n: localized links in {path}")
    return 1 if bad else 0


def cmd_stamp(locale, pages):
    if locale not in LOCALES:
        sys.exit(f"unknown locale {locale}")
    lock = load_lock()
    for page in pages:
        if page not in PAGES:
            sys.exit(f"{page} is not in i18n/config.json pages")
        if not os.path.exists(f"{locale}/{page}.mdx"):
            sys.exit(f"{locale}/{page}.mdx does not exist")
        lock.setdefault(locale, {})[page] = source_hash(page)
    write(LOCK_PATH, json.dumps({l: dict(sorted(lock[l].items())) for l in sorted(lock)}, indent=2) + "\n")
    print(f"i18n: stamped {len(pages)} page(s) for {locale}")
    return 0


def cmd_check():
    failed = cmd_nav(check=True) | cmd_links(check=True)
    lock = load_lock()
    for locale in LOCALES:
        for page in PAGES:
            state = page_state(locale, page, lock)
            if state == "stale":
                print(f"::warning file={locale}/{page}.mdx::{page}.mdx changed since this {locale} translation was made. Retranslate it, then run python3 scripts/i18n-pages.py stamp {locale} {page}.")
            elif state == "missing":
                print(f"::warning::{locale}/{page}.mdx is missing; the {locale} menu shows the English page.")
    for locale in os.listdir("."):
        if locale in LOCALES and os.path.isdir(locale):
            for root, _, files in os.walk(locale):
                for name in files:
                    page = os.path.join(root, name)[len(locale) + 1:].removesuffix(".mdx")
                    if name.endswith(".mdx") and page not in PAGES:
                        print(f"::error file={locale}/{page}.mdx::not in i18n/config.json pages, so no menu links to it")
                        failed = 1
    if not failed:
        print("i18n: translations check passed")
    return failed


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "status":
        return cmd_status()
    if cmd == "nav":
        return cmd_nav(check="--check" in argv)
    if cmd == "links":
        return cmd_links(check="--check" in argv)
    if cmd == "stamp" and len(argv) >= 4:
        return cmd_stamp(argv[2], argv[3:])
    if cmd == "check":
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
