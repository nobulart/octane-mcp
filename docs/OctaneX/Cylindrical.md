Cylindrical projection wraps texture maps on a surface with a cylindrical shape. Cylindrical projections provide a quick way to map a texture on cylindrical-shaped surfaces without too much distortion. However, the seams of the texture may be visible in the render, depending on the shape of the surface.

+-----------------------------------+---------------------------------------------------------+
| ![](images/NewItem_292.png)       | Cylindrical                                             |
|                                   |                                                         |
|                                   | ![](images/Cylindrical_Projection_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+---------------------------------------------------------+

Figure 1: The result of using Cylindrical projection with the Checks texture node

This projection performs cylindrical mapping where the U coordinate is the longitude, and the Y coordinate is the world space Y coordinate. For Images, the mapping on the Y axis maps the image to the \[-1, 1\] interval. For Procedural textures, the W coordinate is the distance from the Y axis. For points on the ground plane (Y = 0), cylindrical and spherical mappings now map to the same points on the images, or what would be the equator on spherical mapping.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_293.png)       | Various Cylindrical Projections                |
|                                   |                                                |
|                                   | ![](images/projectionscylindrical_748x374.png) |
+-----------------------------------+------------------------------------------------+

Figure 2: Cylindrical projections on a box, cylinder, and sphere

The Use Rest Attribute option keeps texture maps from distorting when the geometry is animated.
