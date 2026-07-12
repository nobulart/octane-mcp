The Baking Texture node converts any procedural texture to image texture (Figure 1). For example, if you want to use [Displacement](javascript:void(0);) in Octane, this can only be done with an image texture. With this node, however, it is possible to convert the procedural texture to the image texture and use it in the displacement channel.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_146.png)       | Baking Texture                                |
|                                   |                                               |
|                                   | ![](images/Baking_Texture_Fig01_SE_v2022.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: The Baking Texture node\'s parameters.

 

### Baking Texture Parameters

 

Texture - Accepts any procedural texture.

Enable Baking - Enables the baking process.

Resolution - Determines the resolution of the texture to be converted. Higher resolutions require more RAM and [GPU](javascript:void(0);) power.

Samples per Pixel - Determines how many samples will be used per pixel.

Texture Type - Determines the bit-depth of the bake texture. The options include [LDR](javascript:void(0);) or low dynamic range and HDR Linear Space.

RGB Baking- Converts RGB values according to the type of procedural texture. If the procedural texture has RGB values, enable this option. If the procedural texture uses greyscale values, leave this option off.

Power - Adjusts the intensity value of the baked texture.

[Gamma](javascript:void(0);) - Adjusts the gamma value of the baked texture.

Invert - Inverts the baked texture.

Linear Space Invert - Inverts the image in linear color space.

UV Transform - Positions, rotates, and scales the surface texture.

Projection - Accepts OctaneRender®Projection nodes. If nothing is connected to this input, the Image texture uses the surface\'s UV texture coordinates by default. This also changes the UV set if the original surface contains more than one UV set. For more details, see the Octane [Projections](Projections.md) topic in this manual.

Border Mode U/V - Sets the behavior of the space around the image if it doesn\'t cover the entire geometry. Wrap Around is the default behavior, which repeats the image in the areas outside the image\'s coverage. If you set this parameter to White Color or Black Color, the area outside the image turns to white or black, respectively.

 

In the following example, displacement uses the Turbulence procedural texture by connecting it to the Baking texture node before connecting it to the Displacement node (Figure 2).

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_147.png)       | Baking Texture                                |
|                                   |                                               |
|                                   | ![](images/Baking_Texture_Fig02_SE_v2020.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 2: The Turbulence node used for Displacement by filtering it through the Baking texture node.
