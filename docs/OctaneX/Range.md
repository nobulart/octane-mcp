The Range node is used to remap input values to specific output values (figure 1).

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_269.png)       | Range                                |
|                                   |                                      |
|                                   | ![](images/Range_Fig01_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------+

Figure 1: The Range node used to remap the color intensity of a connected texture map.

 

### Range Parameters

Value - The data to be remapped.

Interpolation - The type of interpolation to be preformed on the data.

Input min/max - The incoming values to be remapped.

Output Min/max - Specifies the output minimum and maximum values

Levels - Determines the number of distinct output levels per channel. This parameter is only active when using the Steps or Posterize interpolation methods.

Clamp - Clamps the input to the input range. Interpolation modes other than Linear are always clamped.
