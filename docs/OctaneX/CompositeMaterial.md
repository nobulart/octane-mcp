The Composite material node mixes several materials using masks (figure 1). This is much cleaner than using several chained Mix materials. If a mask is not connected, the material\'s Opacity is used. The first [Material](javascript:void(0);) pin becomes the base layer.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_87.png)        | Composite Material                                |
|                                   |                                                   |
|                                   | ![](images/Composite_Material_Fig01_SE_v2024.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: A Composite material node used to mix a red and blue [Diffuse material](javascript:void(0);) with a Checks node as a mask

### Composite Material Parameters

Add Input Button - Adds a new Material input to the end of the node.

[Displacement](javascript:void(0);) - Displacement for the Composite Material surface.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

Material - The Material input. When several [Materials](javascript:void(0);) are used, the first Material pin becomes the base layer.

Material Mask - Controls the Material's opacity using an Input map. If a mask is not connected, the Material\'s opacity is used.
