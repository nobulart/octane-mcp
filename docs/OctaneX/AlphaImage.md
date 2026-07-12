The Alpha Image texture utilizes the image\'s native alpha channel to provide transparency. This texture only accepts PNG, TIF, and [EXR](javascript:void(0);) images. It will ignore any information contained in the RGB channels for the texture map and output only the alpha information (Figure 1).

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_143.png)       | Alpha Image                                |
|                                   |                                            |
|                                   | ![](images/Alpha_Image_Fig01_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 1: An Alpha Image node used to mask away parts of a [Glossy material](javascript:void(0);) by connecting the Alpha Image node to the Opacity input.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_144.png)       | Alpha Image                                  |
|                                   |                                              |
|                                   | ![](images/Alpha_Image_Fig02_Nuke_v2020.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 2: The Alpha Image texture map\'s RGB infomation on the left and the alpha information on the right.

 

### Alpha Image Parameters

Power - Controls image brightness. Lowering the value makes the image look darker.

Color Space - Specifies the color space for the imported image.

Legacy [Gamma](javascript:void(0);) - Controls input image luminance, and tunes or color-corrects images if needed, however, this parameter is only used when the Color Space is set to Linear sRGB+Legacy.

Invert - Inverts the texture values.

Linear sRGB Invert - Inverts the image after conversion to linear sRGB color space.

UV Transform - Positions, rotates, and scales the surface texture.

Projection - Accepts OctaneRender® Projection nodes. If nothing is connected to this input, the Image texture uses the surface\'s UV texture coordinates by default. This also changes the UV set if the original surface contains more than one UV set. For more details, see the Octane [Projections](Projections.md) topic in this manual.

Border Mode U/V - Sets the behavior of the space around the image if it doesn\'t cover the entire geometry. Wrap Around is the default behavior, which repeats the image in the areas outside the image\'s coverage. If you set this parameter to White Color or Black Color, the area outside the image turns to white or black, respectively.
