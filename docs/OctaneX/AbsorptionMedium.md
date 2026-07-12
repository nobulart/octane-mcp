Absorption is controlled with the Absorption medium, which defines how fast light is absorbed while passing through a medium. The absorbed light will not continue through the surface and it\'s absorbed energy is converted to the opposed color from the color specified in the Absorption attribute (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_119.png)       | Absorption                                |
|                                   |                                           |
|                                   | ![](images/Absorption_Fig01_SE_v2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Absorption Medium parameters as seen in the NodeGraph Editor with Invert Absorption deactivated.

The color resulting from the absorption is dependent on the distance light travels through the material. With increased distance, it gets darker, and if the absorption is colored, it becomes more saturated. It works in a subtractive manner in that the scattered color is the compliment of the color designated in the parameter (figure 2).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_120.png)       | Scatter Color                             |
|                                   |                                           |
|                                   | ![](images/Absorption_Fig02_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: Complimentary colors

### Absorption Parameters

Density - Determines the density of the particles in the surface. The larger the value, the more likely light will be absorbed when passing through the surface. (figure 2).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_121.png)       | Density                                            |
|                                   |                                                    |
|                                   | ![](images/Absorption_Medium_Fig02_SE_v2020_2.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 3: Increasing the Density parameter.

Volume Step % - Depending on the surface, you may need to adjust this parameter as it is specified as a percentage of the voxel size. The default value is 100%, but if the volume is smaller than this, you need to decrease the value. Decreasing this value decreases render speed, and increasing the value causes the ray marching algorithm to take longer steps. If the Volume Step % exceeds the volume\'s dimensions, then the ray marching algorithm takes a single step through the whole volume. To get the most accurate results, keep Volume Step % as small as possible.

Volume Shadow Ray Step % - Step length that is used by the shadow ray for marching through volumes.

Use Volume Step Length for Volume Shadow Ray Step Length - Check box for using the Volume Step Length for the Volume Shadow Ray Step Length as well.

Sample Position [Displacement](javascript:void(0);) - Allows a texture to control a volume\'s sample positions displacement.

Volume Padding - Expands the volume bounding box by the given percentage in all six directions, but only if sample position displacement is being used. 

Absorption - By default, the absorption attribute is controlled by a value slide ranging from 0 - 1 where 0 is no absorption and 1 is full absorption. A color or texture can be added to replace the value slider. The color\'s value and saturation can be used to further determine the absorption amount. Note: If the Invert Absorption attribute is active, these values will be behave in the opposite fashion, for example: 0 will be full absorption and 1 will be no absorption. (figure 3).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_122.png)       | Greyscale Absorption                               |
|                                   |                                                    |
|                                   | ![](images/Absorption_Medium_Fig03_SE_v2020_2.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 4: Using a grayscale value to control absorption.

Absorption can also be controlled using color values. The observed color is the complementary color (opposite color) of the specified color value if Invert Absorption is deactivated (figure 4).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_123.png)       | Color Absorption                                   |
|                                   |                                                    |
|                                   | ![](images/Absorption_Medium_Fig04_SE_v2020_2.png) |
+-----------------------------------+----------------------------------------------------+

Figure 5: Using color values to determine absorption.

Invert Absorption - Inverts the absorption characteristics so that the absorption color specified is the same color seen in the surface. For example: Red results in red, otherwise, red would result in green (if this check box is inactive).

 

The Schlick node can be used to control which direction the scattering occurs.
