The Hair [Material](javascript:void(0);) has been designed to work with [Alembic](javascript:void(0);) files imported as hair and fur objects. Its parameters are focused on characteristics common with hair and fur strands (Figure 1).

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_90.png)        | Hair Material                                 |
|                                   |                                               |
|                                   | ![](images/Hair_Material_Fig01a_SE_v2020.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: The Hair material assigned to an imported Alembic file.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_91.png)        | Hair Material Parameters                     |
|                                   |                                              |
|                                   | ![](images/Hair_Material_Fig02_SE_v2021.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 2: The Hair Material parameters.

### Hair Material Parameters

Diffuse - Adds an additional layer of color to the hair. This parameters is usually set to a value instead of a color, the color is set in the Diffuse Color parameter. The diffuse parameters are designed to be used when in Albedo mode.

Diffuse Color - Add an additional layer of color to the hair strands. The diffuse parameters are designed to be used when in Albedo mode.

Albedo - The hair base color.

[Specular](javascript:void(0);) - The hair specular or shininess color.

Melanin - The quantity of pigment for the hair base color.

Pheomelanin - The amount of redness in the hair strand.

Mode - Determines whether to use the Albedo or the Melanin/Pheomelanin parameters to determine the hair color.

Index of Refraction - This parameter controls the level of the Fresnel effect on the specular reflection.

Longitudinal Roughness - Controls the roughness along the hair strand.

Azimuthal Roughness - Controls the roughness along a hair strand\'s cross section.

Offset - Scale offset on the surface of the hair. A value of 0 demotes perfectly smooth cylindrical hair. Increasing this value shifts the specular highlight away from a perfectly reflective direction.

Randomness Frequency - Controls the frequency of randomness on the hair for a more believable effect.

Randomness Offset - Works much like a seed value and offsets the randomness effect.

Randomness Intensity - Controls the intensity of the randomness on each hair strand.

Random Albedo - Specifies the target random albedo on the hair. This parameter will only work with the Albedo mode enabled.

Random Roughness - Adds random roughness variations on top of the base roughness.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium.

Opacity - Controls the transparency value of the hair using greyscale values.

Emission -Determines whether the hair material will function as an emission surface.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

Material Layer - Adds a Material Layer above the base material. See the [Material Layers](MaterialLayers.md) topic in this manual for more details.
