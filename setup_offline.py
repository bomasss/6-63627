#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание three.js r160 в ar-site/js/vendor/ для РАБОТЫ БЕЗ ИНТЕРНЕТА
(+ локальные шрифты Oswald/PT Sans). Запускать один раз при наличии сети:

  python setup_offline.py
"""
import os, ssl, sys, urllib.request, zipfile, io

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "ar-site")
VENDOR = os.path.join(SITE, "js", "vendor")
VER = "3.160.0"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60, context=ctx).read()


def main():
    os.makedirs(VENDOR, exist_ok=True)
    print("Скачиваю three.js r160…")
    data = fetch(f"https://github.com/mrdoob/three.js/archive/refs/tags/r160.zip")
    zf = zipfile.ZipFile(io.BytesIO(data))
    prefix = f"three.js-{VER[2:]}/"
    kept = 0
    for name in zf.namelist():
        if not name.startswith(prefix): continue
        rel = name[len(prefix):]
        if rel.startswith("build/three.module.js") or \
           (rel.startswith("examples/jsm/") and rel.endswith(".js")):
            target = os.path.join(VENDOR, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(zf.read(name))
            kept += 1
    print(f"three.js: {kept} файлов в ar-site/js/vendor/")

    # ---- локальные шрифты (Oswald + PT Sans, кириллица) ----
    print("Скачиваю шрифты…")
    css = fetch("https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=PT+Sans:ital,wght@0,400;0,700&display=swap").decode()
    import re
    os.makedirs(os.path.join(SITE, "css", "fonts"), exist_ok=True)
    out_css = []
    for block in css.split("@font-face"):
        pass
    # проще: найдём все url() и скачаем
    urls = sorted(set(re.findall(r"url\((https://[^)]+\.woff2)\)", css)))
    mapping = {}
    for u in urls:
        fname = u.split("/")[-1]
        # имена могут повторяться между семействами — добавим хвост пути
        import hashlib
        h = hashlib.md5(u.encode()).hexdigest()[:6]
        base, ext = os.path.splitext(fname)
        fname = f"{base}-{h}{ext}"
        with open(os.path.join(SITE, "css", "fonts", fname), "wb") as f:
            f.write(fetch(u))
        mapping[u] = "fonts/" + fname
    local = css
    for u, l in mapping.items():
        local = local.replace(u, l)
    with open(os.path.join(SITE, "css", "fonts-local.css"), "w") as f:
        f.write(local)
    print(f"Шрифты: {len(urls)} файлов в ar-site/css/fonts/, подключаются через css/fonts-local.css")
    print("\nГотово! Теперь страницы работают полностью офлайн.")
    print("Чтобы страницы подключили локальные шрифты автоматически, добавьте в build_pages.py")
    print("строку <link ... fonts.googleapis...> -> замените на <link rel='stylesheet' href='../css/fonts-local.css'>")


if __name__ == "__main__":
    main()
