The Analytic lights mimic mesh lights but generate much less noise at lower sampling values than their mesh counterparts (figure 1).

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_317.png)       | Analytic Light                                |
|                                   |                                               |
|                                   | ![](images/Analytic_Light_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: The Analytic light and it\'s associated parameters

### Analytic Light Parameters

Type - Determines the light shape.

Spread Angle - Sets the width of the light source\'s cone of illumination when Quad or Disk light types are selected.

Spread Cutoff Hardness - Sets the edge hardness of the cone of illumination when Quad or Disk light types are selected.

Normalize Power - Keeps the emitted power constant when the angle changes.

Falloff Radius - Determines the falloff distance from the light source.

Use in Post Volume - Enables or disables the light in post volume rendering.

Emission - The emission type can be either a Texture Emission or a Black Body Emission. See the [Mesh Emitters](MeshEmitters.md) section for more details. 

Transform - Contains parameters to move, scale, and rotate the analytic light.

Object Layer - Contains the standard object parameters. See the [Object Layer Node](ObjectLayerNode.md) section for more details.

Quad Size - Determines the size of the light source when Quad is selected as the light type.

Disc Size - Determines the size of the light source when Disk is selected as the light type.

Sphere Radius - Determines the radius of the light source when Sphere is selected as the light type.

Tube Cap Radius - Determines the radius of the light source when Tube is selected as the light type.

Tube Length - Determines the length of the light source when Tube is selected as the light type.
