The Color Key node is used to key out a specified color in a connected texture map (figure 1).

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_258.png)       | Color Key                                |
|                                   |                                          |
|                                   | ![](images/Color_Key_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------+

Figure 1: The Color Key node used to key out the red color on a connected texture map

 

### Color Key Parameters

Input Image - Image to be keyed.

Key Color - The color to be keyed.

Mask - Garbage matte should be connected here.

Fill Color - The color to replace the keyed area.

Low/High Cutoff - The low and high cutoff for the color difference.

Computation [Gamma](javascript:void(0);) - Adjusts the color range midtones before computing the difference.

Projection - Specifies the projection type to be used for this texture.

U Cutoff Low/High - Specifies the low and high edge of simple 2D cutoff in the U direction.

V Cutoff Low/High - Specifies the low and high edge of simple 2D cutoff in the V direction.
