The [Scattering](javascript:void(0);) medium is used to create the look of subsurface scattering. Scattering contains parameters for both scattering and absorption. This is the phenomena where light rays enter a surface, are scattered within the material of surface and then exit again. It is the key to creating the look of realistic human skin and other organic surfaces (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_124.png)       | Scatter Medium                            |
|                                   |                                           |
|                                   | ![](images/Scattering_Fig01_SE_v2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Scattering medium attributes, which include an [Absorption](javascript:void(0);) attribute similar to the Absorption medium

### Scattering Medium Parameters

Density - Determines the density of the particles in the surface. The larger the scale value, the more likely light will be absorbed when passing through the surface.

Volume Step % - Depending on the surface, you may need to adjust this parameter as it is specified as a percentage of the voxel size. The default value is 100%, but if the volume is smaller than this, you need to decrease the value. Decreasing this value decreases render speed, and increasing the value causes the ray marching algorithm to take longer steps. If the Volume Step % exceeds the volume\'s dimensions, then the ray marching algorithm takes a single step through the whole volume. To get the most accurate results, keep Volume Step % as small as possible.

Volume Shadow Ray Step % - Step length that is used by the shadow ray for marching through volumes.

Use Volume Step Length for Volume Shadow Ray Step Length - Check box for using the Volume Step Length for the Volume Shadow Ray Step Length as well.

Single Scatter Amount - Determines how often direct light is calculated in volumes, as a ratio of scatter events.

Sample Position [Displacement](javascript:void(0);) - Allows a texture to control a volume\'s sample positions displacement.

Volume Padding - Expands the volume bounding box by the given percentage in all six directions, but only if sample position displacement is being used. 

[Absorption](javascript:void(0);) - By default, the absorption attribute is controlled by a value slide ranging from 0 - 1 where 0 is no absorption and 1 is full absorption. A color or texture can be added to replace the value slider. The color\'s value and saturation can be used to further determine the absorption amount. Note: If the Invert Absorption attribute is active, these values will be behave in the opposite fashion, for example: 0 will be full absorption and 1 will be no absorption.

Absorption can also be controlled using color values. The observed color is the complementary color (opposite color) of the specified color value if the Invert Absorption parameter is deactivated (figure 2).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_125.png)       | Color Absorption                                   |
|                                   |                                                    |
|                                   | ![](images/Absorption_Medium_Fig04_SE_v2020_2.png) |
+-----------------------------------+----------------------------------------------------+

Figure 2: Using color values to determine absorption.

 

Invert Absorption - Inverts the absorption characteristics so that the absorption color specified is the same color seen in the surface. For example: Red results in red, otherwise, red would result in green (if this check box is inactive).

Scattering - The Scattering value determines how quickly light is scattered as it moves through the surface. A high value means that light is scattered sooner as it enters the surface, a low value means that light passes deeper into the surface before it is scattered. A value of 0 disables scattering entirely. This can be either a grayscale or color texture. When using a float or grayscale texture, values greater than zero determine how quickly the light scatters (figure 3).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_126.png)       | Various Scatter Values                             |
|                                   |                                                    |
|                                   | ![](images/Scattering_Medium_Fig05_SE_v2020_2.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 3: Various float values and their effects on the Scattering parameter.

Phase - The Phase function controls the direction of the  light as it is scattered in the surface. A value of 0 results in light being scattered equally in all directions, positive values result in forward scattering, where the photons continue in roughly the same direction they were going when they entered the surface. Negative values result in backwards scattering where the light moves through the surface in the direction roughly opposite to the angle at which the light entered the surface. Additionally, the Schlick node can be used to control which direction the scattering occurs.

 

Emission - This parameter allows the volume to emit or generate its own illumination.
