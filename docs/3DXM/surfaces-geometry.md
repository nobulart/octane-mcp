# Surfaces Geometry — Revolution, Toroidal, Quadratic

> All surfaces of revolution, toroidal forms, quadratic surfaces, and miscellaneous classes.
> Each has explicit parametric equations suitable for the OctaneX MCP grammar pipeline.

---

## 1. Torus

**Category:** Quadric surface | **Type:** Surface of revolution | **Degree:** 4 (algebraic)

### Parametric Equations
```
x = aa · (cos(v) + u · cos(halftwists · v/2) · cos(v))
y = aa · (sin(v) + u · cos(halftwists · v/2) · sin(v))
z = aa · u · sin(v/2)
```

**Properties:**
- Only few surfaces parameterizable with one patch
- Easiest example for geodesic study
- Geodesic classification: (p,q)-torus knots on surface
  - Geodesic surrounds hole p times, swings up/down q times
  - (7,2)-knot, (11,2)-knot examples
- Geodesic can be near-asymptotic to inner equator

**OctaneX Grammar Mapping:**
- Use `torus.jpg` as reference
- Generate: sweep circle along circular guide path
- Torus knot parametric form:
  ```
  latRad = soulRad + meridRad · cos(meridFreq · t)
  c(t) = [latRad · cos(soulFreq · t), latRad · sin(soulFreq · t), meridRad · sin(meridFreq · t)]
  ```
- half-twists parameter controls topology (Möbius = 1, torus = 0)

---

## 2. Sphere

**Category:** Constant positive curvature | **Type:** Surface of revolution | **Curvature:** K = 1

**Properties:**
- Stereographic projection: conformal from plane
- All points umbilic (equal principal curvatures)
- Polar grid parameterization: meridian/parallel lines

**Visual reference:** `sphere.jpg` (polar_grid_rot_stereogr_005.jpg)

---

## 3. Ellipsoid

**Category:** Quadratic surface | **Type:** Triaxial ellipsoid

**Properties:**
- Four focal conics
- Special case of ellipsoid when two axis lengths equal: spheroid (oblate/prolate)

**Visual reference:** `ellipsoid_4focus.jpg`

---

## 4. Paraboloids

| Type | Equation | Shape |
|---|---|---|
| Elliptic Paraboloid | z = x²/a² + y²/b² | Bowl-shaped |
| Hyperbolic Paraboloid | z = x²/a² - y²/b² | Saddle shape |
| Circular Paraboloid | z = x² + y² | Circular bowl |

**Visual references:** `paraboloid_010.jpg`, `hyperbolic_paraboloid.jpg`

---

## 5. Hyperboloid

| Type | Equation | Sheets |
|---|---|---|
| Hyperboloid of One Sheet | x²/a² + y²/b² - z²/c² = 1 | Connected |
| Hyperboloid of Two Sheet | x²/a² + y²/b² - z²/c² = -1 | Two components |

**Properties:**
- **One sheet:** doubly ruled surface (two families of straight lines)
- **Two sheet:** asymptotic cone at origin

**Visual reference:** `hyperboloid1.jpg` (one sheet)

---

## 6. Quadratic Cone (Double Cone)

**Properties:**
- Limit of hyperboloid as center → origin
- Asymptotic cone for both hyperboloids

---

## 7. Cyclide of Dupin

**Category:** Quartic surface | **Type:** Inversion of torus/cylinder/cone

**Properties:**
- Image of torus under sphere inversion (x ↦ x/|x|²)
- Dupin cyclide = tube surface with sphere centers
- Can be touched from inside and outside by families of spheres
- Generalizes torus, cylinder, cone

**Visual reference:** `clifford_cyclides.jpg`

---

## 8. Bianchi-Pinkall Flat Tori

**Category:** Flat metric tori | **Type:** Isometric embeddings

**Properties:**
- Continuous deformation between flat tori
- Preserves intrinsic flat metric while deforming in R⁴ → R³

**Visual reference:** `Bianchi_Pinkall3.jpg`

---

## 9. Clifford Torus

**Category:** Flat torus | **Type:** Equal radii torus

**Properties:**
- Special torus where major radius = minor radius
- Lies in S³ ⊂ R⁴ as product of equal circles
- Cyclide special case

**Visual reference:** `clifford_cyclides.jpg`

---

## 10. Hopf-Fibered Linked Tori

**Category:** Fiber bundles | **Type:** Torus fibered by circles

**Properties:**
- S³ decomposed into linked circles (Hopf fibration)
- Each circle is a fiber
- Multiple linked tori emerge from the fibration

**Visual reference:** `hopf_fibered_linked_tor_001.jpg`

---

## 11. Monkey Saddle

**Category:** Cubic surface | **Type:** Morse singularity

**Properties:**
- z = x³ - 3xy² (cubic saddle)
- Threefold symmetry: 3 ridges, 3 valleys
- One saddle point with 6 sectors

---

## 12. Kuen Surface

**Category:** Pseudospherical surface | **Type:** K = -1 | **Singularities:** Self-intersection

**Properties:**
- Pseudospherical analog of tractrix surface
- Self-intersecting singularity curve
- Dini deformation family member

**Visual reference:** `kuen_surface.jpg`

---

## 13. Dini Surface

**Category:** Pseudospherical (K = -1) | **Type:** Dini deformation of pseudosphere

**Properties:**
- Pseudosphere with twist (Dini parameter d controls torsion)
- K = -1 for all parameter values
- As d → 0: converges to pseudosphere
- As d → π/2: asymptotic to helicoid

**Visual reference:** `dini_surface.jpg`

---

## 14. Breather & Soliton Surfaces

**Category:** Nonlinear wave surfaces | **Type:** Sine-Gordon equation solutions

| Family | Description |
|---|---|
| Breather | Standing wave on pseudosphere |
| 1-Soliton | Single traveling wave |
| 2-Soliton | Two interacting waves |
| 3-Soliton | Three waves |
| 4-Soliton | Four patches |
| Breather+Soliton | Combined Breather and Soliton |

**Sine-Gordon equation:** q'' = sin(q)

**Visual references:** `Breather_Soliton4-s269x232.png`, `three-soliton_different-s256x244.png`, `Sine-Gordon_4-Soliton_Patch-s289x217.png`

---

## 15. Whinney Umbrella

**Category:** Self-intersecting surface | **Type:** Singularity at origin

**Properties:**
- Double point at origin
- One edge of the self-intersection curve
- Simple polynomial parametrization

---

## 16. Right Conoid

**Category:** Ruled surface | **Type:** Generation by lines through fixed axis

**Properties:**
- Ruled with all rulings meeting a fixed line (axis)
- Plane rotates around axis, generating a line in each position
- Generalizes cylinder and cone

---

## 17. Dirac Belt (Topological Surface)

**Category:** Topological surface | **Type:** Belt trick visualization

**Properties:**
- Demonstrates π₁(so(3)) = Z₂
- Belt twists and untwists through topological trick
- Important for quantum mechanics (spin-1/2 rotation)

**Visual reference:** `eedirac_belt_icon_y78b7-s264x237.png`

---

## 18. Möbius Strip

**Category:** Non-orientable | **Type:** Twist surface | **Boundary:** Single curve

```
Parametric (standard):
x(u,v) = (R + v·cos(u/2)) · cos(u)
y(u,v) = (R + v·cos(u/2)) · sin(u)
z(u,v) = v · sin(u/2)
```

**Properties:**
- One-sided surface
- One boundary component
- 180° twist generates the non-orientability

**Visual reference:** `moebius_strip.jpg`

---

## 19. Klein Bottle

**Category:** Non-orientable | **Type:** Closed surface (no boundary)

**Properties:**
- Immersed in R³ (cannot be embedded)
- Self-intersects in a circle
- Quotient of the torus by antipodal map

**Visual reference:** `klein_bottle.jpg`

---

## 20. Steiner Surface (Roman Surface)

**Category:** Non-orientable | **Type:** Quartic surface

**Properties:**
- Three mutually perpendicular self-intersection lines
- All meet at the triple point (origin)
- Symmetric under coordinate permutations

**Visual reference:** `steiner_surface.jpg`

---

## 21. Constant Width Surfaces

**Category:** Convex surfaces | **Type:** Constant width in all directions

**Properties:**
- A surface where the distance between any two parallel tangent planes is constant
- Generalizes the Reuleaux triangle to 3D
- Meissner bodies are minimum-volume examples

**Visual reference:** `constant_width_1rot_011.jpg`

---

## 22. Snail Shell (Logarithmic Spiral Shell)

**Category:** Natural surface | **Type:** Spiral self-similar surface

**Properties:**
- Grows logarithmically
- Self-similar across scales
- Mathematical model from natural spiral shells

**Visual reference:** `SnailShellOpen.jpg`

---

## References

- All gallery: [virtualmathmuseum.org/Surface/gallery_o.html](https://virtualmathmuseum.org/Surface/gallery_o.html)
- Surfaces PDF: [pdf/Surfaces.pdf](pdf/Surfaces.pdf)
- Ruled Surfaces: [pdf/RuledSurfaces.pdf](pdf/RuledSurfaces.pdf)
- Helicoid-Catenoid: [pdf/Helicoid-Catenoid.pdf](pdf/Helicoid-Catenoid.pdf)
- Triply periodic: [pdf/Schwarz_PD_Family.pdf](pdf/Schwarz_PD_Family.pdf)
- Collected ATOs: [pdf/Collected_ATOs.pdf](pdf/Collected_ATOs.pdf)
