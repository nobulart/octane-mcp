Metallic materials are reflective materials with colored reflections or highlights that come off at different wavelengths, and its reflections are propagated by a full-color [Specular](javascript:void(0);) map (figure 1).

+-----------------------------------+-------------------------------------------------------------+
| ![](images/NewItem_101.png)       | Metallic Materials                                          |
|                                   |                                                             |
|                                   | ![](images/metallicmaterial_fullcolorcompare_SEv3-08-4.png) |
+-----------------------------------+-------------------------------------------------------------+

Figure 1: Metallic materials have full-colored reflections

OctaneRender® has a [Glossy](javascript:void(0);) material node, which by default emulates a diffuse surface with a clear coat. This works well for plastics. A Metallic material works similar to a Glossy material, but the way the channels are combined is more suitable to model metals (figure 2).

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_102.png)       | Fresnel Effect                                         |
|                                   |                                                        |
|                                   | ![](images/metallicmaterial_wwofresnel_SEv3-08-6_.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 2: Without Fresnel effect (left); with Fresnel effect (right)

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_103.png)       | Metallic Meterial Parameters                     |
|                                   |                                                  |
|                                   | ![](images/Metallic_Material_Fig03_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 3: The OctaneRender Metallic material

### Metallic Material Parameters

[Diffuse](javascript:void(0);) Color - The diffuse texture for the Reflection channel.

Specular Color - The specular reflection channel, which determines the metallic color. If the IOR is set to a value less than 0, OctaneRender® adjusts the color brightness to match the Fresnel equations.

Edge Tint - The color of the edges of the metal material, only used with Artistic and IOR+Color modes.

Specular Map - Controls the blend between the Diffuse and Specular channels.

+-----------------------------------+---------------------------------------------------------------+
| ![](images/NewItem_636.png)       | Specular Comparisions                                         |
|                                   |                                                               |
|                                   | ![](images/metallicmaterial_attribute_specularmap_SEv3-0.png) |
+-----------------------------------+---------------------------------------------------------------+

Figure 4: Specular only (left); Specular and Diffuse with Specular map (middle); visualization of the Specular map (right)

BRDF Model - The BRDF (Bidirectional Reflectance Distribution Function) is a function that determines the amount of light reflected from a material when light falls on it. For Metallic materials, there are four applicable BRDF Models to choose from. Each BRDF is affected by a specific geometric property (microfacet distribution) of the surface, which describes the microscopic shape (microfacet normals) of that surface, and it serves as a function to scale the reflections\' brightness in the BRDF. 

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_637.png)       | BRDF Models                                      |
|                                   |                                                  |
|                                   | ![](images/Metallic_Material_Fig05_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 5: The four BRDF Models applicable to Metallic materials

Roughness - Adjusts the Specular reflection channel\'s roughness.

Anisotropy - Controls the material\'s reflectance uniformity. If the reflectance changes based on the orientation or the surface rotation, it is Anisotropic. If the reflectance is uniform in all directions and does not change based on the orientation or surface rotation, it is Isotropic. By default, this attribute is 0 and it sets the Metallic material as Isotropic. Non-zero values mean the material exhibits Anisotropic reflectance, where -1 is horizontal and 1 is vertical.

+-----------------------------------+---------------------------------------------------------------+
| ![](images/NewItem_638.png)       | Anisotropic Roughness                                         |
|                                   |                                                               |
|                                   | ![](images/metallicmaterial_attribute_anisotropy_SEv3-05.png) |
+-----------------------------------+---------------------------------------------------------------+

Figure 6: Anisotropic roughness exemplified in materials like brushed metal

 

Rotation - The rotation of the anisotropic Specular reflection channel.

Spread - Determines the tail spread of the specular BSDF.

Metallic Reflection Mode - This changes how OctaneRender® calculates reflectivity.

- Artistic - Uses the Specular color.
- IOR + Color - Uses the Specular color and adjusts the brightness using the IOR.
- RGB IOR - Uses the three IOR values (for 650nm, 550nm, and 450 nm) and ignores the Specular color.

Index Of Refraction - Complex-valued IOR (n-k\*i) controlling the specular reflection\'s Fresnel effect, where n = the refractive index and k = the attenuation or extinction coefficient. For RGB mode, the IOR for red light (650nm).

Index Of Refraction (Green) - For RGB mode, the IOR for red light (550nm).

Index Of Refraction (Blue) - For RGB mode, the IOR for red light (450nm).

Allow Caustics - If enabled, the photon tracing kernel will create caustics for light reflecting or transmitting through the object.

Sheen - The subtle lustre\'s color on the material\'s surface.

Sheen Roughness - The Roughness channel for the sheen that is present on Metallic and Glossy materials.

Film Width - Simulates the look of a thin film of material on the surface. This is useful when you want to create an effect such as the rainbow colors that appear on an oil slick surface. Larger values increase the effect\'s strength.

Film IOR - Controls the thin film\'s IOR by adjusting its visible colors.

Opacity - Controls the Toon material\'s transparency with a Grayscale texture.

Bump - Simulates a relief using a Grayscale texture interpreted as a Height map.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map.

Normal - Distorts normals based on an RGB image.

[Displacement](javascript:void(0);) - Creates very detailed geometry with a low memory footprint.

Smooth - Enables or disables normal interpolation. If normal interpolation is disabled, triangle meshes appear faceted.

Smooth Shadow Terminator - If enabled, self-intersecting shadows are smoothed according to the polygon\'s curvature.

Round Edges - Rounds the geometry edges by using a shading effect rather than creating additional geometry. For more information, see the [Round Edges](RoundEdges.md) topic in this manual.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

[Material](javascript:void(0);) Layer - Adds a Material layer above the base material. See the Material Layers topic in this manual for more details.
