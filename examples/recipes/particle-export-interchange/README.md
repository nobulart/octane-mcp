# Particle Export Interchange (C5)

Phase C interchange stress test: the same SPlisHSPlasH-derived particle cloud is emitted as CSV, VTK PolyData, and partio .bgeo, then rendered in OctaneX as instanced spheres (one group per phase). CSV + VTK round-trips are asserted equal. partio is not installable on CPython 3.12, so the .bgeo is emitted but not parsed here.
