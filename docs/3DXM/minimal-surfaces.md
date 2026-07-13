# Minimal Surfaces

> Minimal surface: a surface with zero mean curvature at every point. First discovered in the
> 19th century, these surfaces model soap films and are fundamental to differential geometry.

## Parametric Minimal Surface Theory

All minimal surfaces can be represented via the **Weierstrass representation**:
given analytic functions g(z) (Gauss map) and f(z)dz (Weierstrass differential), the surface is:

```
X(u,v) = Re ∫ (1-g², i(1+g²), 2g) · f dz
```

The associate family parameter `aa` morphs between minimal surfaces while preserving the metric.

---

## 1. Catenoid

**Category:** Classic minimal surface | **Type:** Ruled | **Curvature:** K ≤ 0

```
x(t, v) = cosh(v) · cos(at)
y(t, v) = cosh(v) · sin(at)
z(t, v) = at
```

**Properties:**
- Surface of revolution of the catenary y = cosh(x)
- Two parallel circular coaxial rings bound a unique catenoid soap film
- First minimal surface after the plane (1744, Euler)
- **Bifurcation:** At critical ring separation, two catenoids exist; beyond, none

**OctaneX Grammar Mapping:**
- Use `catenoid_range_001.jpg` as visual reference
- Parametric surface: generate from revolution of catenary profile
- Tube rendering: natural as swept surface along circular guides
- Associated helicoid (isometric deformation via parameter aa from 0 to π/2)

---

## 2. Helicoid

**Category:** Ruled minimal surface | **Type:** Screw motion | **Curvature:** K ≤ 0

**Parametric Equations:**
```
Px = bb · (cos(aa) · sinh(v) · sin(u) + sin(aa) · cosh(v) · cos(u))
Py = bb · (-cos(aa) · sinh(v) · cos(u) + sin(aa) · cosh(v) · sin(u))
Pz = bb · (cos(aa) · u + sin(aa) · v)
```

**Properties:**
- Like a spiral staircase; infinite ruled surface
- Each ruling line intersects the central axis perpendicularly
- **Helix connection:** The evolute of a helix is another helix of the same curvature
- **Oloid:** Convex hull of the osculating circles of the helix-evolute pair

**OctaneX Grammar Mapping:**
- Use `helicoid_catenoid_001.jpg` as morphing reference
- Generate by revolving a line through a screw motion
- Tube cross-section shows straight symmetry lines (helicoid) and meridian lines (catenoid)
- Wireframe rendering reveals ruled structure clearly

---

## 3. Scherk Surface

**Category:** Periodic minimal surface | **Type:** Graph + implicit | **Curvature:** K ≤ 0

### Scherk's Doubly Periodic Surface
```
x = u
y = v  
z = (ln(cos(a·v) / cos(a·u))) / a
```
- Graph representation (function f(x,y) = z)
- Infinite checkerboard of saddle pieces
- Vertical lines at checkerboard vertices (invisible in graph form)

### Scherk's Singly Periodic Surface
```
sin(z) - sinh(x)·sinh(y) = 0
```
- Implicit equation (more versatile for raytracing)
- Conjugate to doubly periodic Scherk

**Properties:**
- Heinrich Scherk (1834) — first new minimal surfaces after 50-year gap
- Fundamental to the Weierstrass representation revolution of the 1980s
- **Curvature circles:** At each point, the two principal curvature circles have equal radius but lie on opposite sides of the surface

---

## 4. Enneper Surface

**Category:** Finite total curvature | **Type:** Polynomial immersion | **Curvature:** K ≤ 0

**Classical Parametric Equations:**
```
x = u - u³/3 + u·v²
y = v - v³/3 + v·u²  
z = u² - v²
```

**Properties:**
- Gauss map: g(z) = z^k where k = ee + 1
- Cartesian grid lines = principal curvature lines
- Polar form: every second radial parameter line is a symmetry line
- Higher-order symmetries (3-fold, 6-fold) found in the 1980s

**Far-away asymptotic:**
```
x(t) = R·cos(3t),  y(t) = R·sin(3t),  z(t) = h·cos(2t)
```

**OctaneX Grammar Mapping:**
- Use `enneper2_polar.jpg` for rotational symmetry visualization
- Polynomial parametrization → efficient mesh generation
- Higher symmetry variants: set ee for k-fold symmetry
- Associate family generates Wavy Enneper, Planar Enneper, Catenoid-Enneper

---

## 5. Costa Surface

**Category:** Triply periodic candidate | **Type:** Infinite total curvature | **Curvature:** K ≤ 0

**Properties:**
- Discovery of the first explicitly described minimal surface that is embedded (Costa, 1982)
- Topology: punctured torus with two catenoid-like ends
- Constructed from the Weierstrass data of elliptic functions

**OctaneX Grammar Mapping:**
- Use `costa_011.jpg` as reference
- Mesh from the Weierstrass data parametrization
- Connects to Kummer minimal surface (algebraic, but self-intersecting)

---

## 6. Gyroid

**Category:** Triply periodic minimal surface | **Type:** Embedded, screw symmetry | **Curvature:** K ≤ 0

**Properties:**
- Discovered by Alan Schoen (~1970)
- **Key distinction:** NOT cut by straight symmetry lines or planar symmetry curves into simple pieces
- Triply embedded: interface between two different polymeres
- Lies in the associate family between Schwarz P-surface and Schwarz D-surface
- **Symmetry:** 3-axis rotation (120°) at 12 polar centers

**Associate family:** Schwarz P ⟷ Gyroid ⟷ Schwarz D
- Gyroid associate parameter: ~0.577 (~52°)
- Fundamental cell: rhombohedral with all edge lengths equal

**OctaneX Grammar Mapping:**
- Use `gyroid_08476.jpg` as reference (or fetched from `i/gyroid_assoc_patch_001.png`)
- Implicit formulation ideal for raytracing in OctaneX
- Hexagonal tiling pattern visible in cross-section
- Material scientist importance: TPMS (Triply Periodic Minimal Surface) classification

---

## 7. Schwarz PD Family (P-surface, D-surface)

**Category:** Triply periodic surfaces | **Type:** Weierstrass representation | **Curvature:** K ≤ 0

**P-surface (primitive cubic):**
```
Implicit: cos(x) + cos(y) + cos(z) = 0
```

**D-surface (diamond):**
```
Implicit: cos(s)·cos(c) + cos(t)·cos(c) + cos(u)·cos(c) = 0
```
where s,x + t,y + u,z = π

**Properties:**
- Both P and D are embedded with reflection symmetries
- Genus 3 per fundamental domain
- **Schwarz H family:** triangular catenoids (equilateral triangle boundaries) vs. Schwarz PD's square catenoids
- **Lidinoid:** found by Swedish chemist Lidin (1991) in the associate family of PD

**OctaneX Grammar Mapping:**
- Use `schwarz_h_family_morph.jpg` for PD morphing visualization
- Square boundaries give regular mesh layout
- TPMS class for material science visualization

---

## 8. Saddle Tower

**Category:** Periodic minimal surface | **Type:** Weierstrass construction | **Curvature:** K ≤ 0

**Properties:**
- Generalization of Scherk's singly periodic surface
- "Stacked" saddle pieces connected by handles
- N-fold symmetry for saddle tower with N-fold twist

**OctaneX Grammar Mapping:**
- Use `scherk_rotate_001.jpg` for rotation visualization
- Morph between single saddle tower and multi-saddle configurations

---

## 9. Delaunay Surfaces (Constant Mean Curvature)

**Category:** Surfaces of revolution with H = constant | **Type:** Ruled/unduloid | **Curvature:** K varies

| Surface | Shape | Description |
|---|---|---|
| Unduloid | Wavy cylinder | Delaunay's undulation |
| Catenoid | H = 0 limit | Minimal surface |
| Nodoid | Node surface | Self-intersecting variant |
| Cylinder | H = 1/2R | Constant |
| Sphere | H = 1/R | Special case |

### Unduloid
**Category:** CMC surface | **Type:** Wave profile | **Mean Curvature:** H = 1

```
Parametric form from Delaunay rolling ellipse
```

**OctaneX Grammar Mapping:**
- Use `unduloid.jpg` as visual reference
- Sweep profile curve (unduloid) around axis
- Parametric: radius varies with sinusoidal oscillation

---

## 10. Pseudosphere & Pseudospherical Surfaces (K = -1)

**Category:** Constant negative curvature | **Type:** Tractrix rotation | **Gauss Curvature:** K = -1

### Pseudosphere
```
Parametric by tractrix rotation
x = cosh(u)·cos(v)
y = cosh(u)·sin(v)  
z = u - tanh(u)
```

### Conic K = -1 Surface Family
**ODE:** q''(u) = sin(q(u))
The Dini parameter `d` controls the twisting deformation.

**Properties:**
- K = -1 surface: hyperbolic geometry at the surface level
- Dini deformation: family of K=-1 surfaces from the pseudosphere by twist
- Pseudosphere: surface of revolution of the tractrix (1693)

**OctaneX Grammar Mapping:**
- Use `pseudosphere.jpg` and `dini_surface.jpg` as references
- Tractrix curve profile → sweep around axis
- Kuen surface (branch): self-intersecting singularity

---

## 11. Boy's Surface & Cross-Cap

**Category:** Non-orientable surfaces | **Type:** Immersions | **Genus:** Non-orientable

### Boy's Surface
```
Apery parametrization: rational map from R² → R³
```

**Properties:**
- Smallest immersion of the real projective plane in R³
- 3-fold rotational symmetry
- Discovered by Werner Boy (1901), computed by Apery
- **Bryant-Kusner variant:** conformal immersion

### Cross-Cap
**Properties:**
- Immersion of projective plane with one triple point
- Simpler but more singular than Boy's surface
- Self-intersection: one double curve crossing at one point

**OctaneX Grammar Mapping:**
- Use `moebius_strip.jpg` and `cross_cap.jpg` as references
- Rational polynomial parametrization → efficient meshing
- 3-fold symmetry gives nice rotational visualization

---

## 12. Möbius Strip & Steiner Surface

**Category:** Non-orientable surfaces | **Type:** Immersion

### Möbius Strip
**Properties:**
- One-sided surface: single boundary curve
- 180° half-twist generates from rectangle

### Steiner Surface (Roman Surface)
**Properties:**
- Self-intersecting projective plane
- Three double lines meeting at one triple point
- Steiner's Romansche Fläche (1844)

---

## 13. Cyclides

**Category:** Dupin cyclides | **Type:** Inversion of torus | **Curvature:** K varies

**Definition:** Images of tori under sphere inversion (x ↦ x/|x|²)
- Also images of Dupin cyclides
- Touched by 1-parameter families of spheres (from inside and outside)

**OctaneX Grammar Mapping:**
- Use `clifford_cyclides.jpg` for torus-to-cyclide morph
- Cyclide = torus under inversion → compute via point transformation
- Clifford torus is the special case where torus center = inversion center

---

## Weierstrass Representation (Master Formula)

All these minimal surfaces arise from Weierstrass data (g, f):

```
X(u,v) = Re ∫ (1-g², i(1+g²), 2g) · f dz

Mean curvature H = 0 ⟺ minimal
Isometric deformation preserves first fundamental form
```

**Associate family parameter aa:** varies from 0 to π/2, smoothly morph between conjugate minimal surfaces.

## Key Relationships

```
Plane
  └── isometric to Catenoid ⟶ Helicoid (via aa parameter)
  └── conjugate to Scherk (doubly periodic) ⟶ Scherk (singly periodic)
  └── conjugate to Enneper
  
Costa Surface
  └── conjugate = Kummer surface (self-intersecting)
  
Schwarz P-surface ⟷ Gyroid ⟷ Schwarz D-surface
  └── associate family morphing
  
Delaunay family: Catenoid (H=0) ⟶ Unduloid ⟶ Cylinder ⟶ Sphere (H max)
```

## References

- **PDFs:** `pdf/Surfaces.pdf`, `pdf/CatalanHennebergScherk.pdf`, `pdf/Helicoid-Catenoid.pdf`, `pdf/Enneper_Surface.pdf`, `pdf/Costa.pdf`, `pdf/Schwarz_H_Family.pdf`, `pdf/RuledSurfaces.pdf`
- **Collected ATOs:** `pdf/Collected_ATOs.pdf` (7MB master catalog of all 3DXM exhibits)
- **Research Papers:** Karcher (1988) "Embedded Minimal Surfaces Derived From Scherk's Examples"; DHKW (1991) "Minimal Surfaces I"
- **All exhibits:** [virtualmathmuseum.org/Surface/gallery_m.html](https://virtualmathmuseum.org/Surface/gallery_m.html)
