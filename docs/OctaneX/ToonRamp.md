The Toon Ramp controls the amount of detail in toon shading. It provides the positions for mapping a range of colors to the Toon material's [Diffuse](javascript:void(0);) channel or [Specular](javascript:void(0);) channel, and the resulting color range is based on the hue set by that respective channel. You can add more positions to increase the number of colors in the range. The Toon Ramp is applied to the Toon Diffuse Ramp or Toon Specular Ramp of a Toon material node. The Toon Ramp can be accessed from the [Materials](javascript:void(0);) category in the Nodegraph Editor.

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_116.png)       | Toon Ramp                               |
|                                   |                                         |
|                                   | ![](images/Toon_Ramp_Fig01_SE_2023.jpg) |
+-----------------------------------+-----------------------------------------+

Figure 1: Example of a Toon Ramp

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_644.png)       | Toon Ramp                                      |
|                                   |                                                |
|                                   | ![](images/toonramp_nodeconnect_SEv3-08-4.png) |
+-----------------------------------+------------------------------------------------+

Figure 2: The Toon Ramp applied to a Toon material

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_645.png)       | Toon Ramp                                      |
|                                   |                                                |
|                                   | ![](images/toonramp_albedorange_SEv3-08-4.png) |
+-----------------------------------+------------------------------------------------+

Figure 3: The resulting range of the albedo value with a Toon Ramp applied

 

### Toon Ramp Parameters

Interpolation - This determines how the colors blend.

![](images/toonramp_interpolationconstant_SEv3-08-4.png)

Figure 4: Constant Interpolation

![](images/toonramp_interpolationlinear_SEv3-08-4.png)

Figure 5: Linear Interpolation

Interpolation Color Space - The color space in which colors are combined between control points. Physical uses linear values and creates gradients that approximate optical effects in the real world. Perceptual uses the Oklab color space and creates gradients that vary moothly to the human eye. 

Start Value - The output value at the 0 position.

End Value - The output value at the 1.0 position.

Position 1 - A position that sets the boundary between the Start Value and the End Value.

Value 1 - The output value at position 1.
