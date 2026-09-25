/* ============================================================
   ВЬЮПОР ЭКСПОНАТА
   - Загружает .glb/.gltf из ../models/ (можно перетаскиванием)
   - Вращение пальцем / мышью, pinch-to-zoom, автовращение
   - Кнопка «СМОТРЕТЬ В AR» — WebXR AR на Android
     (на iPhone/iPad открывает Quick Look при наличии USDZ)
   - Работает и без интернета: three.js берётся из js/vendor/,
     если его нет — с CDN
   ============================================================ */
(function () {
  "use strict";

  /* EXHIBIT_ID вшивается при сборке страницы build_pages.py.
     Для ручного открытия можно также передать ?id=... */
  const id = (typeof EXHIBIT_ID !== "undefined" && EXHIBIT_ID)
    ? EXHIBIT_ID
    : new URLSearchParams(location.search).get("id");
  const exhibit = EXHIBITS.find(e => e.id === id) || EXHIBITS[0];

  /* ---------- заполнение страницы данными ---------- */
  document.title = exhibit.title + " — Ар-музей «Оружие Победы»";
  const $ = s => document.querySelector(s);
  $("#ex-id").textContent = "Экспонат № " + exhibit.index;
  $("#ex-category").textContent = exhibit.category;
  $("#ex-title").textContent = exhibit.title;
  $("#ex-subtitle").textContent = exhibit.subtitle;
  const factsBox = $("#facts-list");
  exhibit.facts.forEach((f, i) => {
    const row = document.createElement("div");
    row.className = "fact";
    row.innerHTML = '<span class="fact-num">' + String(i + 1).padStart(2, "0") + "</span><p></p>";
    row.querySelector("p").textContent = f;
    factsBox.appendChild(row);
  });

  /* ---------- three.js: локальный js/vendor/ или CDN (importmap) ---------- */
  async function loadThree() {
    const THREE = await import("three");
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
    return { THREE, OrbitControls, GLTFLoader };
  }

  /* ---------- сцена ---------- */
  const viewerEl = $("#viewer");
  const overlay = $("#overlay");
  const overlayText = $("#overlay-text");
  const hint = $("#hint");
  let renderer, scene, camera, controls, model, autoRotate = true, running = false;

  function showOverlay(text, spinner) {
    overlay.classList.remove("hidden");
    overlayText.textContent = text;
    overlay.querySelector(".spinner").style.display = spinner ? "" : "none";
  }
  function hideOverlay() { overlay.classList.add("hidden"); }

  function initScene() {
    const w = viewerEl.clientWidth, h = viewerEl.clientHeight;
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(w, h);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    if ("outputColorSpace" in renderer) renderer.outputColorSpace = THREE.SRGBColorSpace;
    viewerEl.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, w / h, 0.01, 200);
    camera.position.set(2.2, 1.6, 2.6);

    scene.add(new THREE.HemisphereLight(0xffffff, 0xb8b2a0, 1.6));
    const key = new THREE.DirectionalLight(0xfff4e0, 2.2);
    key.position.set(3, 5, 2);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xdfe8ff, 0.7);
    fill.position.set(-4, 2, -3);
    scene.add(fill);

    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(6, 64),
      new THREE.ShadowMaterial({ opacity: 0.14 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    const grid = new THREE.GridHelper(12, 24, 0xb9b3a2, 0xd9d4c6);
    grid.position.y = 0.001;
    scene.add(grid);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.4;
    controls.minDistance = 0.4;
    controls.maxDistance = 20;
    controls.target.set(0, 0.5, 0);

    controls.addEventListener("start", () => {
      hint.classList.add("hidden");
      if (autoRotate) { controls.autoRotate = false; }
    });

    window.addEventListener("resize", () => {
      const w2 = viewerEl.clientWidth, h2 = viewerEl.clientHeight;
      camera.aspect = w2 / h2; camera.updateProjectionMatrix();
      renderer.setSize(w2, h2);
    });

    running = true;
    (function loop() {
      if (!running) return;
      requestAnimationFrame(loop);
      controls.update();
      renderer.render(scene, camera);
    })();
  }

  function frameObject(obj) {
    const box = new THREE.Box().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3()).length() || 1;
    const center = box.getCenter(new THREE.Vector3());
    obj.position.sub(center);
    obj.position.y += size / 2;            // ставим на «пол»
    const pivot = new THREE.Group();
    pivot.add(obj);
    scene.add(pivot);
    camera.position.set(size * 1.1, size * 0.75, size * 1.35);
    controls.target.set(0, size / 2, 0);
    controls.update();
    return pivot;
  }

  /* ---------- заглушка, пока .glb не положен в models/ ---------- */
  function buildPlaceholder() {
    const g = new THREE.Group();
    const matBody = new THREE.MeshStandardMaterial({ color: 0x5a6146, roughness: 0.75, metalness: 0.15 });
    const matDark = new THREE.MeshStandardMaterial({ color: 0x2c2f28, roughness: 0.6, metalness: 0.3 });
    const matRed  = new THREE.MeshStandardMaterial({ color: 0x8e2f24, roughness: 0.5 });

    const hull = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.55, 1.3), matBody);
    hull.position.y = 0.55; hull.castShadow = true; g.add(hull);

    const glacis = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.4, 1.28), matBody);
    glacis.position.set(1.25, 0.45, 0); glacis.rotation.z = -0.5; glacis.castShadow = true; g.add(glacis);

    const turret = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.68, 0.42, 24), matBody);
    turret.position.set(-0.15, 1.02, 0); turret.castShadow = true; g.add(turret);

    const gun = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.075, 1.7, 12), matDark);
    gun.rotation.z = Math.PI / 2; gun.position.set(1.05, 1.02, 0); gun.castShadow = true; g.add(gun);

    for (const side of [-1, 1]) {
      const track = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.42, 0.3), matDark);
      track.position.set(0, 0.32, side * 0.78); track.castShadow = true; g.add(track);
      for (let i = -2; i <= 2; i++) {
        const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.1, 20), matBody);
        wheel.rotation.x = Math.PI / 2;
        wheel.position.set(i * 0.55, 0.32, side * 0.93);
        g.add(wheel);
      }
    }
    const star = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.03, 5), matRed);
    star.rotation.x = Math.PI / 2; star.position.set(-0.15, 1.24, 0.001); g.add(star);

    return frameObject(g);
  }

  /* ---------- загрузка реальной модели ---------- */
  let THREE, OrbitControls, GLTFLoader, gltfLoader = null;
  async function loadModel(url, nameForError) {
    showOverlay("Загрузка модели…", true);
    try {
      if (!gltfLoader) gltfLoader = new GLTFLoader();
      const gltf = await new Promise((res, rej) => gltfLoader.load(url, res, undefined, rej));
      if (model) { scene.remove(model); }
      model = frameObject(gltf.scene);
      gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
      hideOverlay();
      $("#btn-reset").disabled = false;
      $("#btn-ar").disabled = !xrSupported && !isiOS();
    } catch (err) {
      showOverlay(
        "Файл «" + (nameForError || exhibit.model_file) + "» не найден в папке models/. " +
        "Показана интерактивная заглушка — её тоже можно вращать. " +
        "Положите .glb-файл модели в ar-site/models/ (или перетащите сюда) — и она загрузится.",
        false
      );
      if (!model) model = buildPlaceholder();
      $("#btn-reset").disabled = false;
      setTimeout(() => overlay.classList.remove("hidden"), 0);
      setTimeout(hideOverlay, 6500);
    }
  }

  /* ---------- AR: WebXR / Quick Look ---------- */
  let xrSupported = false, xrSession = null;
  async function checkXR(THREE_) {
    try {
      xrSupported = !!(navigator.xr && await navigator.xr.isSessionSupported("immersive-ar"));
    } catch (e) { xrSupported = false; }
    const btn = $("#btn-ar");
    if (isiOS()) {
      btn.disabled = false;              // попробуем Quick Look (нужен .usdz рядом с моделью)
      btn.title = "На iPhone нужен файл .usdz с таким же именем, что и модель";
    } else if (xrSupported) {
      btn.disabled = false;
    } else {
      btn.disabled = true;
      btn.title = "AR доступен в Chrome на Android; на ПК используйте вращение мышью";
    }
  }
  function isiOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }

  async function startAR() {
    if (isiOS()) {   // Quick Look
      const usdz = "../models/" + exhibit.model_file.replace(/\.(glb|gltf)$/i, "") + ".usdz";
      const a = document.createElement("a");
      a.rel = "ar"; a.href = usdz;
      document.body.appendChild(a); a.click(); a.remove();
      return;
    }
    if (!xrSupported || !renderer.xr) return;
    try {
      xrSession = await navigator.xr.requestSession("immersive-ar", {
        requiredFeatures: ["hit-test"], optionalFeatures: ["dom-overlay"],
        domOverlay: { root: document.body }
      });
      renderer.xr.setReferenceSpaceType("local");
      await renderer.xr.setSession(xrSession);
      scene.children.forEach(c => {           // скрыть «студию»: сетку и пол
        if (c.isGridHelper || (c.isMesh && c.material && c.material.type === "ShadowMaterial")) c.visible = false;
      });
      if (model) {                            // уменьшим и поставим перед пользователем
        model.scale.multiplyScalar(0.5);
        model.position.set(0, 0, -1);
      }
      xrSession.addEventListener("end", () => {
        xrSession = null;
        scene.children.forEach(c => { c.visible = true; });
        if (model) { model.scale.multiplyScalar(2); model.position.set(0, 0, 0); }
      });
    } catch (e) { console.warn("AR:", e); }
  }

  /* ---------- кнопки ---------- */
  function wireButtons() {
    $("#btn-rotate").addEventListener("click", (ev) => {
      autoRotate = !autoRotate;
      controls.autoRotate = autoRotate;
      ev.currentTarget.classList.toggle("active", autoRotate);
    });
    $("#btn-rotate").classList.toggle("active", autoRotate);

    $("#btn-reset").addEventListener("click", () => {
      if (!model) return;
      const box = new THREE.Box().setFromObject(model);
      const size = box.getSize(new THREE.Vector3()).length() || 1;
      camera.position.set(size * 1.1, size * 0.75, size * 1.35);
      controls.target.set(0, size / 2, 0);
      controls.update();
    });

    $("#btn-ar").addEventListener("click", startAR);

    $("#btn-upload").addEventListener("click", () => $("#file-input").click());
    $("#file-input").addEventListener("change", (ev) => {
      const f = ev.target.files[0];
      if (f) loadModel(URL.createObjectURL(f), f.name);
    });

    /* перетаскивание файла прямо на вьюпорт */
    ["dragover", "drop"].forEach(t =>
      viewerEl.addEventListener(t, ev => { ev.preventDefault(); ev.stopPropagation(); }));
    viewerEl.addEventListener("drop", ev => {
      const f = ev.dataTransfer.files[0];
      if (f) loadModel(URL.createObjectURL(f), f.name);
    });
  }

  /* ---------- старт ---------- */
  (async function boot() {
    try {
      const mod = await loadThree();
      THREE = mod.THREE;
      OrbitControls = mod.OrbitControls;
      GLTFLoader = mod.GLTFLoader;
    } catch (e) {
      showOverlay("Не удалось загрузить three.js. Положите библиотеку в ar-site/js/vendor/ (см. README) и обновите страницу.", false);
      return;
    }
    initScene();
    wireButtons();
    await checkXR();
    model = buildPlaceholder();          // сразу показываем заглушку
    loadModel("../models/" + exhibit.model_file);
  })();
})();
