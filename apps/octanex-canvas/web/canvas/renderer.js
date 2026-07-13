// OctaneX Agentic Canvas — three.js live renderer (Phase 2).
//
// Hydrates a `canvas.scene.v1` JSON (emitted by WebGLBackend on the Python side)
// into an interactive WebGL scene. No Octane required: this runs entirely in the
// browser, which is the central UX unlock of the canvas build plan.
//
// Controls are implemented inline (spherical-orbit + pan + wheel-zoom) rather than
// pulling three's OrbitControls example module, because the gateway serves these
// files as plain static assets and WKWebView has no ES-module import map to
// resolve `import ... from 'three'`. The relative import below resolves fine.

import * as THREE from "../vendor/three.module.js";

const OBJECT_TYPES = new Set([
  "box", "sphere", "ellipsoid", "cylinder", "mesh",
  "polyline", "points", "arrow", "text_label",
]);

export class CanvasRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    this.root = new THREE.Group(); // holds the built scene graph
    this.scene.add(this.root);

    this.materialCache = new Map();
    this.objectNodes = new Map(); // id -> { node, meta }
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();

    // Orbit state
    this.target = new THREE.Vector3(0, 0, 0);
    this.spherical = new THREE.Spherical();
    this._dragging = false;
    this._panning = false;
    this._lastX = 0;
    this._lastY = 0;
    this.onPick = null;

    this._bindControls();
    this._resize();
    window.addEventListener("resize", () => this._resize());
  }

  // ---- public API -------------------------------------------------------- //

  setScene(sceneJson) {
    this._disposeScene();
    this._currentScene = sceneJson || {};
    this._applyEnvironment(this._currentScene.environment || {});
    this._buildObjects(this._currentScene.objects || []);
    this._applyCamera(this._currentScene.camera || {});
    return this;
  }

  start() {
    if (this._running) return this;
    this._running = true;
    const loop = () => {
      if (!this._running) return;
      this._update();
      this.renderer.render(this.scene, this.camera);
      this._raf = requestAnimationFrame(loop);
    };
    this._raf = requestAnimationFrame(loop);
    return this;
  }

  stop() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    return this;
  }

  snapshot() {
    // Browser-side snapshot path (Phase 2/6). Returns a PNG data URL.
    this.renderer.render(this.scene, this.camera);
    return this.canvas.toDataURL("image/png");
  }

  getCameraState() {
    return {
      position: this.camera.position.toArray().map((n) => +n.toFixed(3)),
      target: this.target.toArray().map((n) => +n.toFixed(3)),
      fov: this.camera.fov,
    };
  }

  // ---- scene construction ------------------------------------------------ //

  _applyEnvironment(env) {
    const bg = env.background || "#070a0e";
    this.scene.background = new THREE.Color(bg);
    // Reset lights each rebuild.
    this._lights = this._lights || [];
    this._lights.forEach((l) => this.scene.remove(l));
    this._lights = [];
    const ambient = new THREE.AmbientLight(0xffffff, 0.45);
    const key = new THREE.DirectionalLight(0xffffff, 1.1);
    key.position.set(5, 8, 6);
    const rim = new THREE.DirectionalLight(0x88aaff, 0.5);
    rim.position.set(-6, 2, -4);
    this.scene.add(ambient, key, rim);
    this._lights = [ambient, key, rim];
  }

  _material(mat) {
    mat = mat || {};
    const m = new THREE.MeshStandardMaterial({
      color: new THREE.Color(mat.color || "#cccccc"),
      roughness: mat.roughness ?? 0.6,
      metalness: mat.metalness ?? 0.0,
      transparent: (mat.opacity ?? 1.0) < 1.0,
      opacity: mat.opacity ?? 1.0,
      wireframe: !!mat.wireframe,
    });
    if (mat.emissive) {
      m.emissive = new THREE.Color(mat.emissive);
      m.emissiveIntensity = mat.emissiveIntensity ?? 1.5;
    }
    return m;
  }

  _resolveMaterial(id, materials) {
    if (this.materialCache.has(id)) return this.materialCache.get(id);
    const def = (materials || []).find((m) => m.id === id) || {};
    const m = this._material(def);
    this.materialCache.set(id, m);
    return m;
  }

  _buildObjects(objects) {
    this.materialCache.clear();
    const materials = (this._currentScene && this._currentScene.materials) || [];
    for (const o of objects) {
      if (!OBJECT_TYPES.has(o.type)) continue;
      if (o.type === "text_label") continue; // CSS2D later; not a 3D node
      const node = this._geometryFor(o, materials);
      if (!node) continue;
      node.position.fromArray(o.position || [0, 0, 0]);
      if (o.rotation) node.rotation.fromArray(o.rotation);
      this.root.add(node);
      this.objectNodes.set(o.id, { node, meta: o });
    }
  }

  _geometryFor(o, materials) {
    const mat = this._resolveMaterial(o.material, materials);
    const scale = o.scale || [1, 1, 1];
    switch (o.type) {
      case "box": {
        const g = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), mat);
        g.scale.fromArray(scale);
        return g;
      }
      case "sphere":
      case "ellipsoid": {
        const g = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24), mat);
        g.scale.fromArray(scale);
        return g;
      }
      case "cylinder": {
        const g = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 1, 24), mat);
        g.scale.fromArray(scale);
        return g;
      }
      case "polyline": {
        // Build a point set: use explicit points if given, otherwise synthesise a
        // clear ring so an "orbit"/"ring" intent always reads as a ring even if
        // the planner emits a degenerate path.
        let pts = (o.points || []).map((p) => new THREE.Vector3().fromArray(p));
        if (pts.length < 3) {
          const R = 1.8;
          pts = [];
          for (let i = 0; i <= 48; i++) {
            const a = (i / 48) * Math.PI * 2;
            pts.push(new THREE.Vector3(R * Math.cos(a), R * Math.sin(a) * Math.sin(0.38), R * Math.sin(a) * Math.cos(0.38)));
          }
        }
        const curve = new THREE.CatmullRomCurve3(pts);
        const radius = o.radius || 0.035;
        const g = new THREE.Mesh(
          new THREE.TubeGeometry(curve, Math.max(12, pts.length * 4), radius, 10, false),
          mat
        );
        return g;
      }
      case "points": {
        const pts = (o.points || []).map((p) => new THREE.Vector3().fromArray(p));
        if (!pts.length) return null;
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        return new THREE.Points(geo, new THREE.PointsMaterial({ size: o.radius || 0.05, color: mat.color }));
      }
      default:
        return null; // mesh/arrow: later phases
    }
  }

  _applyCamera(cam) {
    const pos = cam.position || [4, 3, 4];
    this.target.fromArray(cam.target || [0, 0, 0]);
    const offset = new THREE.Vector3().fromArray(pos).sub(this.target);
    this.spherical.setFromVector3(offset);
    this.camera.fov = cam.fov || 45;
    this.camera.updateProjectionMatrix();
    this._syncCamera();
  }

  _syncCamera() {
    const off = new THREE.Vector3().setFromSpherical(this.spherical);
    this.camera.position.copy(this.target).add(off);
    this.camera.lookAt(this.target);
  }

  // ---- controls ---------------------------------------------------------- //

  _bindControls() {
    const c = this.canvas;
    c.addEventListener("pointerdown", (e) => {
      this._lastX = e.clientX;
      this._lastY = e.clientY;
      this._downX = e.clientX;
      this._downY = e.clientY;
      if (e.button === 2 || e.shiftKey) this._panning = true;
      else this._dragging = true;
      this._moved = false;
    });
    window.addEventListener("pointerup", (e) => {
      const moved = Math.hypot(e.clientX - this._downX, e.clientY - this._downY);
      if (!moved && this.onPick) this._tryPick(e);
      this._dragging = false;
      this._panning = false;
    });
    window.addEventListener("pointermove", (e) => {
      if (!this._dragging && !this._panning) return;
      const dx = e.clientX - this._lastX;
      const dy = e.clientY - this._lastY;
      this._lastX = e.clientX;
      this._lastY = e.clientY;
      this._moved = true;
      if (this._panning) this._pan(dx, dy);
      else this._orbit(dx, dy);
    });
    c.addEventListener("wheel", (e) => {
      e.preventDefault();
      const k = Math.pow(0.95, -e.deltaY * 0.01);
      this.spherical.radius = Math.max(0.5, Math.min(120, this.spherical.radius * k));
      this._syncCamera();
    }, { passive: false });
    c.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  _orbit(dx, dy) {
    this.spherical.theta -= dx * 0.005;
    this.spherical.phi = Math.max(0.05, Math.min(Math.PI - 0.05, this.spherical.phi - dy * 0.005));
    this._syncCamera();
  }

  _pan(dx, dy) {
    const dist = this.spherical.radius;
    const panScale = dist * 0.0015;
    const right = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 1);
    this.target.addScaledVector(right, -dx * panScale);
    this.target.addScaledVector(up, dy * panScale);
    this._syncCamera();
  }

  _tryPick(e) {
    const rect = this.canvas.getBoundingClientRect();
    this.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const nodes = Array.from(this.objectNodes.values()).map((x) => x.node);
    const hits = this.raycaster.intersectObjects(nodes, false);
    if (hits.length && this.onPick) {
      const id = this._idForNode(hits[0].object);
      if (id) this.onPick(id, this.objectNodes.get(id).meta);
    }
  }

  _idForNode(node) {
    for (const [id, v] of this.objectNodes) if (v.node === node) return id;
    return null;
  }

  // ---- loop / resize ----------------------------------------------------- //

  _update() {
    // Hook for future animation; nothing time-dependent yet.
  }

  _resize() {
    const w = this.canvas.clientWidth || this.canvas.parentElement.clientWidth || window.innerWidth;
    const h = this.canvas.clientHeight || this.canvas.parentElement.clientHeight || window.innerHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / Math.max(1, h);
    this.camera.updateProjectionMatrix();
  }

  _disposeScene() {
    for (const { node } of this.objectNodes.values()) {
      this.root.remove(node);
      if (node.geometry) node.geometry.dispose();
    }
    this.objectNodes.clear();
    this.materialCache.forEach((m) => m.dispose());
    this.materialCache.clear();
  }
}
