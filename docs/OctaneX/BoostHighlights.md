The Boost Highlights Output AOV node can be used to adjust the highlights of a composite or components of a composite node tree (figure 1).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_555.png)       | Boost Highlights                               |
|                                   |                                                |
|                                   | ![](images/Boost_Highlights_Fig01_SE_2024.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: The Boost Highlights Output AOV node used to adjust the Threshold settings of the Reflection AOV in a composite node tree

### Boost Highlights Parameters

Enabled - Determines whether Boost Highlights is active or not.

Multiplier - Sets the maximum slope of the luminance curve to apply. The curve ramps from a slope of 1.0 at Threshold to a slope of Multiplier at Threshold + Threshold Softness. 

Threshold - The minimum input luminance value for scaling to occur. This determines which pixels are considered highlights and has no effect on any pixels with luminance less than or equal to this value. 

Threshold Softness - The amount of extra input luminance required on top of Threshold to reach the full Multiplier scale factor for each additional unit of input luminance.
