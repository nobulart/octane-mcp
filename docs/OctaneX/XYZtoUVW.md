XYZ To UVW is also known as planar projection or flat mapping. This mapping type takes the coordinates in world or object space and uses them as UVW coordinates. For images, only the X and Y coordinates are relevant, which are mapped to U and V. In other words, the images use flat mapping projected along the Z axis. XYZ To UVW results vary, depending on whether it is applied to a Procedural texture or an imported texture. In Figure 1, a procedural texture using XYZ To UVW is oriented in a similar fashion to Box projection. In Figure 2, an imported texture using XYZ To UVW is oriented in a planar fashion.

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_306.png)       | XYZ to UVW Procedural Texture                       |
|                                   |                                                     |
|                                   | ![](images/XYZ_UVW_Projection_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: XYZ To UVW projection applied to a Procedural texture map

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_307.png)       | XYZ to UVW Imported Texture Map                     |
|                                   |                                                     |
|                                   | ![](images/XYZ_UVW_Projection_Fig02_Nuke_v2020.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 2: XYZ to UVW projection applied to an imported texture map

XYZ To UVW maps image textures to the (-1, -1) - (1, 1) range. Rotating the mapping around the Z axis rotates the image around the center, as the UVW rotation would do. OctaneRender® uses the object coordinate space in a way that the texture projection is in a coordinate space local to each instance. If UV mapping is required, you can apply a transformation in UV space (translation/scale/rotation) via the UV Transform pin. The Use Rest Attribute option keeps texture maps from distorting when the geometry is animated.
