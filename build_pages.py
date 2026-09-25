#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка самостоятельных страниц экспонатов из шаблона + js/viewer.js.
Каждая страница: ar-site/pages/<id>.html, без связей между собой.
Использование:  python build_pages.py
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "ar-site")
PAGES = os.path.join(SITE, "pages")
THREE_VERSION = "0.160.0"
TEMPLATE_FONTS = '<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=PT+Sans:ital,wght@0,400;0,700&display=swap" rel="stylesheet">'

TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f4f2ec">
<title>__TITLE__ — Ар-музей «Оружие Победы»</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=PT+Sans:ital,wght@0,400;0,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/style.css">
<!-- three.js: локально из js/vendor/, либо с CDN (когда есть интернет) -->
<script type="importmap">
{
  "imports": {
    "three": "../js/vendor/three.module.js",
    "three/addons/": "../js/vendor/examples/jsm/",
    "three-cdn": "https://cdn.jsdelivr.net/npm/three@__THREEVER__/build/three.module.js",
    "three/addons-cdn/": "https://cdn.jsdelivr.net/npm/three@__THREEVER__/examples/jsm/"
  }
}
</script>
</head>
<body>
<header class="topbar">
  <svg class="star" viewBox="0 0 24 24"><path d="M12 .9l2.9 6.2 6.8.8-5 4.6 1.3 6.7L12 15.9 6 19.2l1.3-6.7-5-4.6 6.8-.8z"/></svg>
  <span class="brand">Ар-музей · Оружие Победы</span>
  <span class="ex-id" id="ex-id">Экспонат</span>
</header>

<main>
  <div class="exhibit-head">
    <span class="category" id="ex-category"></span>
    <h1 id="ex-title"></h1>
    <p class="subtitle" id="ex-subtitle"></p>
  </div>

  <section class="viewer-card">
    <div class="viewer" id="viewer">
      <div class="overlay" id="overlay">
        <div class="spinner"></div>
        <p id="overlay-text">Загрузка…</p>
      </div>
      <div class="viewer-hint" id="hint">
        <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4z" opacity=".9"/></svg>
        Вращайте пальцем · щипок — приблизить
      </div>
    </div>
    <div class="viewer-toolbar">
      <button class="vbtn active" id="btn-rotate" title="Автовращение">↻ Вращение</button>
      <button class="vbtn" id="btn-reset" disabled>⊙ Сброс</button>
      <button class="vbtn" id="btn-upload" title="Загрузить .glb файл">📁 Модель</button>
      <button class="vbtn primary" id="btn-ar" disabled>AR</button>
      <input type="file" id="file-input" accept=".glb,.gltf,model/gltf-binary" hidden>
    </div>
  </section>

  <section class="facts">
    <h2>Интересные факты</h2>
    <div id="facts-list"></div>
  </section>

  <footer class="site">
    <span class="ribbon">★ ★ ★</span><br>
    Локальный стенд выставки · страница открывается по QR-коду
  </footer>
</main>

<script src="../js/data.js"></script>
<script type="module">
const EXHIBIT_ID = "__ID__";
try { await import("three"); } catch (e) {
  /* локального three.js нет — переписываем map на CDN и ставим flag */
  window.__THREE_CDN__ = true;
}
__VIEWER_JS__
</script>
</body>
</html>
"""


def parse_exhibits():
    """Берём список id/title из js/data.js (без Node)."""
    src = open(os.path.join(SITE, "js", "data.js"), encoding="utf-8").read()
    ids = re.findall(r'id:\s*"([^"]+)"', src)
    titles = re.findall(r'title:\s*"([^"]+)"', src)
    return list(zip(ids, titles))


def main():
    viewer = open(os.path.join(SITE, "js", "viewer.js"), encoding="utf-8").read()
    # импорт three: через importmap, с запасным вариантом на CDN
    viewer = viewer.replace('await import("three")',
                            'await import(window.__THREE_CDN__ ? "three-cdn" : "three")')
    viewer = viewer.replace('await import("three/addons/controls/OrbitControls.js")',
                            'await import((window.__THREE_CDN__ ? "three/addons-cdn/" : "three/addons/") + "controls/OrbitControls.js")')
    viewer = viewer.replace('await import("three/addons/loaders/GLTFLoader.js")',
                            'await import((window.__THREE_CDN__ ? "three/addons-cdn/" : "three/addons/") + "loaders/GLTFLoader.js")')

    # если выполнены setup_offline.py — переключаем страницы на локальные шрифты
    fonts_link = ('<link rel="stylesheet" href="../css/fonts-local.css">'
                  if os.path.exists(os.path.join(SITE, "css", "fonts-local.css")) else
                  '<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=PT+Sans:ital,wght@0,400;0,700&display=swap" rel="stylesheet">')

    os.makedirs(PAGES, exist_ok=True)
    for eid, title in parse_exhibits():
        html = (TEMPLATE
                .replace("__ID__", eid)
                .replace("__TITLE__", title)
                .replace("__THREEVER__", THREE_VERSION)
                .replace("__VIEWER_JS__", viewer)
                .replace(TEMPLATE_FONTS, fonts_link))
        out = os.path.join(PAGES, eid + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("written:", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
