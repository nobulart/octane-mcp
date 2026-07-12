The [Specular](javascript:void(0);) layer is used for shiny materials like plastics, or clear materials like glass. Refer to the [Glossy](javascript:void(0);), Specular, and Universal [Material](javascript:void(0);) topics in this manual for more information.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_100.png)       | Specular Layer                                |
|                                   |                                               |
|                                   | ![](images/Specular_Layer_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: Specular layer parameters

 

### Specular Layer Parameters

Enabled - Determines whether the material layer contributes to the overall layered material system.

Specular - The layer\'s coating color.

[Transmission](javascript:void(0);) - The layer\'s transmission color.

BRDF Model - The BRDF (Bidirectional Reflectance Distribution Function) is a function that determines the amount of light reflected from a material when light falls on it. For Metallic materials, there are four applicable BRDF Models to choose from. Each BRDF is affected by a specific geometric property (microfacet distribution) of the surface, which describes the microscopic shape (microfacet normals) of that surface, and it serves as a function to scale the reflections\' brightness in the BRDF. 

Roughness - Controls the distribution of the reflections on the surface. Higher values will produce a rougher surface reflection.

Affect Roughness - The percentage of roughness affecting subsequent layers\' roughness.

Anisotropy - The layer\'s anisotropy. A value of -1 is horizontal, while 1 is vertical. A value of 0 is Isotropic.

Rotation - The rotation of the specular anisotropic reflection.

Spread - Determines the tail spread of the specular BSDF.

IOR - The specular reflection\'s or transmission\'s Index Of Refraction.

1/IOR Map - The Index of Refraction map. Each texel represents 1/IOR. When this is empty, OctaneRender® uses the IOR value. If this is not empty, then this parameter overrides the Index Of Refraction set by the IOR value.

Allow Caustics - If enabled, the photon tracing kernel will create caustics for light reflecting or transmitting through the object.

Film Width - Sets the film coating\'s thickness.

Film IOR - Sets the film coating\'s Index Of Refraction.

Thin Layer - Makes the layer very thin so it reflects, or goes straight though the layer.

Bump - Simulates a relief by using a Greyscale texture interpreted as a Height map for the layer.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map.

Normal - Distorts layer normals using an RGB image.

Dispersion Coefficient - This is the B parameter of the Cauchy dispersion model. Increasing this value increases the coloration amount and dispersion in the layer's transmission and caustics.

Layer Opacity - Controls the layer\'s opacity with a Greyscale texture.
