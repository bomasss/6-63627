Сюда положите файлы моделей в формате .glb (или .gltf) со следующими именами:

  suvorov-uniform.glb   WW2 Soviet Uniform
  russian-pilot.glb     Russian Pilot
  il2-sturmovik.glb     Ilyushin Il-2 Sturmovik
  yak-9.glb             Yak-9
  t-34.glb              Tank T-34
  bmp-1.glb             BMP-1
  t-34-85.glb           T-34-85
  t-70.glb              T-70

Имена задаются в ar-site/js/data.js (поле model_file) — можно переименовать
файлы или поменять значение в data.js, затем выполнить: python build_pages.py

Для AR на iPhone/iPad (Quick Look) желателен additionally файл .usdz
с тем же базовым именем, например il2-sturmovik.usdz.

Пока файла нет — страница показывает интерактивную заглушку (тоже вращается).
