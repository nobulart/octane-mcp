Toon materials have shadows and highlights that appear as blocks of color, resulting in a flat image with fewer shading colors and a distinct colored ink used for outlines and contour lines. The Toon material can create Toon shaders and emulate a cartoonish style of two-dimensional illustrations. Toon materials require a Toon lighting node in order to work. They can also accept a Toon ramp to add a color range for the shader's Diffuse channel (albedo color) or to the shader's Specular channel (Figure 2).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_115.png)       | Toon Material                                |
|                                   |                                              |
|                                   | ![](images/Toon_Material_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: Toon material parameters

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_641.png)       | Toon Ramp                                           |
|                                   |                                                     |
|                                   | ![](images/toonmaterial_node_connect_SEv3-08-4.png) |
+-----------------------------------+-----------------------------------------------------+

Figure 2: A Toon Ramp connected to a Toon material node\'s [Diffuse](javascript:void(0);) ramp input pin

 

### Toon Material Parameters

Diffuse - The Diffuse reflection channel, or the albedo value of the Toon shader.

[Specular](javascript:void(0);) - The Specular reflection channel, which behaves like a coating on top of the Diffuse layer and creates a highlight on the surface depending on the incident light angle and the camera's viewpoint. A value of 0 means there is no highlight at all.

Roughness - The Specular reflection channel\'s roughness. The appearance of the Toon shading's Specular reflection becomes more prevalent as the roughness of the Specular reflection channels decreases.

Toon Lighting Mode - Since Toon Lighting is required for Toon materials to work, this attribute defines where the Toon lighting is drawn from. This can be from the camera direction, or from OctaneRender® Toon Lights. If Toon Lights is the selected mode, Toon materials will need either a Toon point light or a Toon directional light included in the scene in order to work (Figure 4).

+-----------------------------------+---------------------------------------------------------------+
| ![](images/NewItem_642.png)       | Lighting Modes                                                |
|                                   |                                                               |
|                                   | ![](images/toonmaterial_inspector_lightingmode_SEv3-08-4.png) |
+-----------------------------------+---------------------------------------------------------------+

Figure 3: Toon Lighting mode attributes

If Toon Lights is the selected Toon Lighting mode, a Toon Light node must be present in the scene in order for Toon materials to work (figure 4).

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_643.png)       | Toon Light Node                        |
|                                   |                                        |
|                                   | ![](images/Toon_Material_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------+

Figure 4: A Toon Light node

 

Toon Diffuse Ramp - The color/float range that defines how the Toon shading's albedo value (or diffuse color) varies over a surface.

Toon Specular Ramp - The color/float range that defines how the Toon shading's Specular value varies over a surface.

Outline Color - The color used for the surface\'s outline and contour edges.

Outline Thickness - Defines and propagates the outline and contour edges used in the Toon shading. A thickness of 0.0 means there is no outline for that surface.

Opacity - Controls the Toon material transparency with a Grayscale texture.Bump - Simulates a relief using a Grayscale texture interpreted as a height map.

Bump - Creates fine details on the material's surface using a Procedural or Image texture. Often a Greyscale image texture connects to this parameter - light areas of the texture indicate protruding bumps, and dark areas indicate indentation. You can adjust the Bump map\'s strength by adjusting the Power or [Gamma](javascript:void(0);) values on the Image texture node.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map. 

Normal - Distorts normals based on an RGB image.

[Displacement](javascript:void(0);) - Creates very detailed geometry with a low memory footprint.

Smooth - Enables normal interpolation. If disabled, triangle meshes will appear faceted.

Smooth Shadow Terminator - If enabled, self-intersecting shadows are smoothed according to the polygon\'s curvature.

Round Edges - Rounds the geometry edges by using a shading effect rather than creating additional geometry. Refer to the [Round Edges](RoundEdges.md) topic in this manual for more information.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

 

For more information on how to use the Toon material, please see the [Toon Shading](ToonShading.md) topic in this manual.
