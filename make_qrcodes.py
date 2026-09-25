#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация QR-кодов для локальной AR-выставки.

  python make_qrcodes.py                 # IP определится автоматически
  python make_qrcodes.py --ip 192.168.1.50 --port 8000
  python make_qrcodes.py --url http://my-laptop.local:8000   # готовый базовый URL

Результат: ar-site/qrcodes/<id>.png (по одному коду на страницу) + _all_urls.txt
QR ведёт напрямую на страницу экспоната; страницы между собой не связаны.
"""
import argparse, os, socket, subprocess, sys

try:
    import qrcode
except ImportError:
    sys.exit("Нужна библиотека qrcode:  pip install qrcode pillow")

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "ar-site")
OUT = os.path.join(SITE, "qrcodes")


def parse_exhibits():
    """Читаем id и заголовки из ar-site/js/data.js без Node."""
    import re
    src = open(os.path.join(SITE, "js", "data.js"), encoding="utf-8").read()
    ids = re.findall(r'id:\s*"([^"]+)"', src)
    titles = re.findall(r'title:\s*"([^"]+)"', src)
    return list(zip(ids, titles))


def detect_ip():
    """IP ноутбука в локальной Wi-Fi сети."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", default=None, help="IP ноутбука в локальной сети")
    ap.add_argument("--port", type=int, default=8000, help="порт сервера (default 8000)")
    ap.add_argument("--url", default=None, help="готовый базовый URL вместо ip/port")
    args = ap.parse_args()

    base = args.url or f"http://{args.ip or detect_ip()}:{args.port}"
    base = base.rstrip("/")

    exhibits = parse_exhibits()
    os.makedirs(OUT, exist_ok=True)
    lines = []
    for eid, title in exhibits:
        url = f"{base}/pages/{eid}.html"
        qr = qrcode.QRCode(border=3, box_size=12)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1d1f22", back_color="white")
        path = os.path.join(OUT, eid + ".png")
        img.save(path)
        lines.append(f"{title:28s} {url}")
        print("QR:", os.path.relpath(path, ROOT), "->", url)

    with open(os.path.join(OUT, "_all_urls.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nБазовый адрес: {base}")
    print("Отсканируйте любой код телефоном в той же сети.")
    print("Не забудьте: файлы моделей .glb должны лежать в ar-site/models/ с именами из js/data.js")


if __name__ == "__main__":
    main()
