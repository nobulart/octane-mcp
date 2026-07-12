The Null [Material](javascript:void(0);) node is used for mesh objects that have an invisible surface but contain a medium. This is equivalent to setting up a specular material with IOR 1 and a reflection of 0 and a transmission of 1. However, that methodology no longer makes sense with nested dielectric. The Null Material was created to make a medium with no surface work in all cases.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_106.png)       | Null Material                                |
|                                   |                                              |
|                                   | ![](images/Null_Material_Fig01_SE_v2022.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: The Null Material parameters.

 

### Null Material Parameters

Medium - Accepts any medium node.

Opacity - Controls the transparency of the material via a greyscale texture.

Affect Alpha - If enabled, refractions will affect the alpha channel.

[Displacement](javascript:void(0);) - Accepts any displacement node to create highly detailed geometry with a low memory footprint.

Smooth - If disabled, normal interpolation will be disabled and triangle meshes will appear facetted.

Smooth Shadow Terminator - If enabled, self-intersecting shadows are smoothed according to the polygon\'s curvature.

Round Edges - Rounds the geometry edges by using a shading effect, rather than creating additional geometry. See the [Round Edges](RoundEdges.md) topic in this manual for more information.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium
