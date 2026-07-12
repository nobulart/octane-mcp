The Metallic layer is used for highly reflective materials that have colored reflections. 

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_97.png)        | Metallic Layer                                |
|                                   |                                               |
|                                   | ![](images/Metallic_Layer_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: Metallic layer parameters

### Metallic Layer Parameters

Enabled - Determines whether the material layer contributes to the overall layered material system.

[Specular](javascript:void(0);) - The specular reflection channel, which determines the metallic color. If the IOR is set to a value less than 0, OctaneRender® adjusts the color brightness to match the Fresnel equations.

Edge Tint - The color of the edges of the metal material, only used with Artistic and IOR+Color modes.

BRDF Model - The BRDF (Bidirectional Reflectance Distribution Function) is a function that determines the amount of light reflected from a material when light falls on it. For Metallic materials, there are four applicable BRDF Models to choose from. Each BRDF is affected by a specific geometric property (microfacet distribution) of the surface, which describes the microscopic shape (microfacet normals) of that surface, and it serves as a function to scale the reflections\' brightness in the BRDF. 

Roughness - The Metallic layer\'s roughness.

Anisotropy - Controls the material\'s reflectance uniformity. If the reflectance changes based on the orientation or the surface rotation, it is Anisotropic. If the reflectance is uniform in all directions and does not change based on the orientation or surface rotation, it is Isotropic. By default, this attribute is 0 and it sets the Metallic material as Isotropic. Non-zero values mean the material exhibits Anisotropic reflectance, where -1 is horizontal and 1 is vertical.

Rotation - The Metallic Anisotropic reflection\'s rotation.

Spread - Determines the tail spread of the specular BSDF.

Metallic Reflection Mode - This changes how OctaneRender® calculates reflectivity.

- Artistic - Uses the Specular color.
- IOR + Color - Uses the Specular color and adjusts the brightness using the IOR.
- RGB IOR - Uses the three IOR values (for 650nm, 550nm, and 450 nm) and ignores the Specular color.

Index Of Refraction - Complex-valued Index Of Refraction controlling the Metallic reflection\'s Fresnel effect, where n = the refractive index, and k = the extinction coefficient.

Allow Caustics - If enabled, the photon tracing kernel will create caustics for light reflecting or transmitting through the object.

Film Width - Sets the film coating\'s thickness.

Film IOR - This sets the film coating\'s Index Of Refraction.

Bump - Simulates a relief using a Greyscale texture interpreted as a Height map for the layer.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map.

Normal - Distorts the layer normals using an RGB image.

Layer Opacity - Controls the layer\'s opacity with a Greyscale texture.
