The [Glossy](javascript:void(0);) material is used for shiny materials such as plastics or metals (figure 1).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_89.png)        | Glossy Material                                |
|                                   |                                                |
|                                   | ![](images/Glossy_Material_Fig01_SE_v2021.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: The OctaneRender® [Glossy material](javascript:void(0);)

### Glossy Material Parameters

[Diffuse](javascript:void(0);) - Gives the material its color, which is referred to as base color or albedo. You can set Diffuse color by using a value, or by connecting a Procedural or Image texture.

[Specular](javascript:void(0);)- Determines the intensity for specular reflections on the surface. This parameter accepts color, values, or textures. In most cases, specular highlights are white or colorless. However, to simulate metallic surfaces, you should tint the specular color using a color similar to the Diffuse parameter, like the bright yellow-orange highlights seen on a polished copper kettle. A black Diffuse color, a Roughness of 0, and an Index of 0 produces a perfect mirror.

Diffuse BRDF Model - Provides three models for diffuse light reflectance. Lambertian reflects light equally in all directions and does not support roughness. The Octane option creates a sheen effect much like velvet. And, the Oren-Nayar option behaves more like clay.

BRDF Model- The BRDF (Bidirectional Reflectance Distribution Function) determines the amount of light that a material reflects when light falls on it. For Glossy materials, you can choose from six BRDF models. Specific geometric properties (the micro-facet distribution) of the surface affects each BRDF, which describes the surface\'s microscopic shape (i.e. micro-facet normals) and scales the brightness of the BRDF\'s reflections. 

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_630.png)       | BRDF Models                                    |
|                                   |                                                |
|                                   | ![](images/Glossy_Material_Fig02_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 2: The four BRDF Models applicable to Glossy materials

Roughness - Determines how much Specular reflection spreads across the surface - also known as reflection blur. This parameter accepts a value, color, or texture map (Procedural or Image). A value of 0 simulates a perfect, smooth reflective surface like a mirror. Increasing the value simulates micro-facets in the surface, which causes reflective highlights to spread. To create a worn plastic look, increase the Roughness value.

Anisotropy - Controls the material\'s reflectance uniformity. Reflectance changes based on surface orientation or rotation is anisotropic. If the reflectance is uniform in all directions and doesn\'t change based on the surface\'s orientation or rotation, then it is isotropic. This parameter\'s default value is 0, which sets the metallic material as isotropic. Non-zero values mean the material exhibits anisotropic reflectance, where -1 is horizontal and 1 is vertical.

+-----------------------------------+---------------------------------------------------------------+
| ![](images/NewItem_631.png)       | Anisotropy                                                    |
|                                   |                                                               |
|                                   | ![](images/metallicmaterial_attribute_anisotropy_SEv3-08.png) |
+-----------------------------------+---------------------------------------------------------------+

Figure 3: Anisotropic roughness exemplified in materials like brushed metal

Rotation - The rotation of the anisotropic Specular reflection channel.

Spread - The spread of the tail when using the STD BSDF model.

Film Width - Simulates the look of thin film material on a surface, like creating a rainbow color effect that appears on an oil slick\'s surface. Larger values increase the effect\'s strength.

Film IOR - Controls the film Index of Refraction. This option adjusts the visible colors in the film.

Sheen - The material\'s sheen color.

Sheen Roughness - Roughness channel for the sheen present on Metallic and Glossy materials.

Index Of Refraction - Determines the reflection strength on the surface based on Fresnel\'s law. With a value greater than 1, reflection is strongest on the surface parts that turn away from the viewer\'s angle (grazing angles), while the reflection appears weaker on the surface parts perpendicular to the viewing angle. This results in a more realistic-looking surface. With a value lower than 1, the Fresnel effect is disabled, and the reflection color appears as a uniform color across the highlight. The Specular channel\'s color determines the reflective highlight\'s color.

In the following examples, the six balls have a roughness of 0, 0.2, 0.4, 0.6, 0.8, and 1.0 (left to right,) with the Specular and Index Of Refraction parameters modified for each rendered image (see Figure 3).

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_632.png)       | Specular & IOR                           |
|                                   |                                          |
|                                   | ![](images/GlossyMaterialFig02_SEv4.png) |
+-----------------------------------+------------------------------------------+

Figure 4: Spheres rendered using different settings for Specular and Index Of Refraction

Allow Caustics - If enabled, the photon tracing kernel will create caustics for light reflecting or transmitting through the object.

Opacity - Determines what surface parts are visible in the render. Dark values indicate transparent areas, and light values indicate opaque areas. Values between light and dark create the look of semi-transparent areas. You can lower the Opacity value to fade the object\'s overall visibility, or you can use a Texture map to vary the surface\'s opacity. For example, if you want to make a simple polygon plane look like a leaf, you connect a black-and-white image of the leaf\'s silhouette to the Diffuse shader\'s Opacity channel. When you use an Image texture map, set the Data type to Alpha Image if the image has an alpha channel, or Grayscale image for black-and-white images, to load an image for setting transparency. Use the image\'s Invert checkbox to invert the transparency regions.

Bump - Creates fine details on material surfaces using a Procedural or Image texture. When you connect a Grayscale image texture to this parameter, light areas indicate protruding bumps, and dark areas indicate indentations. You can adjust the Bump map strength by setting the Power or [Gamma](javascript:void(0);) values on the Grayscale image texture node. The [Textures](Textures.md) topic in this manual covers these attributes in more detail.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map.

Normal - Creates the look of fine detail on the surface. A Normal map is a special type of Image texture that uses red, green, and blue color values to perturb the surface normals at render time, thus giving the appearance of added detail. They can be more accurate than Bump maps, but require specific software, such as ZBrush®, Mudbox®, Substance Designer, xNormal, or others to generate. to load a full color Normal map, set the Normal channel to the RGB Image data type. Normal maps take precedence over Bump maps, so you can not use a Normal map and a Bump map at the same time.

[Displacement](javascript:void(0);) - Adjusts surface vertices\' height at render time using a Texture map. Displacement maps differ from Bump or Normal maps by having the texture alter the geometry, as opposed to creating the appearance of detail on the surface. Displacement mapping is more complex than Bump or Normal mapping, but results are more realistic, such as a surface\'s silhouette. The [Textures](Textures.md) topic in this manual covers Displacement mapping in more detail.

Smooth - Smooths out the transition between surface normals by blending polygon edges together. When disabled, the edges between surface polygons appear sharp, giving the surface a faceted look.

Smooth Shadow Terminator - If enabled, self-intersecting shadows are smoothed according to the polygon\'s curvature.

Round Edges - Rounds the geometry edges by using a shading effect, rather than creating additional geometry. See the [Round Edges](RoundEdges.md) topic in this manual for more information.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

[Material](javascript:void(0);) Layer - Adds a Material Layer above the base material. See the [Material Layers](MaterialLayers.md) topic in this manual for more details.
