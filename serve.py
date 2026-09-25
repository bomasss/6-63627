#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Локальный сервер AR-выставки. Хостит ar-site/ на 0.0.0.0 (доступ из Wi-Fi).

  python serve.py            # порт 8000
  python serve.py 8080       # свой порт

После запуска сервер сам определит IP ноутбука и сгенерирует свежие QR-коды,
чтобы они всегда вели на актуальный адрес.
"""
import os, sys, functools, http.server, socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "ar-site")


def lan_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        if not ip.startswith("127."): return ip
    except OSError:
        pass
    return "127.0.0.1"


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # модели и текстуры могут грузиться как module/cross-origin — отключим кэш на время сборки
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        if path.endswith(".glb"): return "model/gltf-binary"
        if path.endswith(".gltf"): return "model/gltf+json"
        if path.endswith(".usdz"): return "model/vnd.usdz+zip"
        return super().guess_type(path)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    # перегенерируем QR под текущий IP/порт
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "make_qrcodes.py"),
                    "--ip", lan_ip(), "--port", str(port)], check=False)

    handler = functools.partial(Handler, directory=SITE)
    with socketserver.ThreadingTCPServer(("0.0.0.0", port), handler) as httpd:
        httpd.allow_reuse_address = True
        print("=" * 56)
        print("  АР-МУЗЕЙ «ОРУЖИЕ ПОБЕДЫ» — сервер запущен")
        print(f"  На ноутбуке : http://localhost:{port}/index.html")
        print(f"  Телефоны    : http://{lan_ip()}:{port}/pages/<экспонат>.html")
        print(f"  Печать QR   : http://{lan_ip()}:{port}/qr-print.html")
        print("  Остановка   : Ctrl+C")
        print("=" * 56)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановлено.")


if __name__ == "__main__":
    main()
