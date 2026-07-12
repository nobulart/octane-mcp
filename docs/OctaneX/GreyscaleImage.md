The Greyscale image converts an RGB image to grayscale. This can conserve RAM when you\'re using a color image as an input for Bump or Opacity channels of an OctaneRender® material. The Invert checkbox inverts the image (useful for Bump and Opacity maps).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_148.png)       | Greyscale Image                                |
|                                   |                                                |
|                                   | ![](images/Greyscale_Image_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: Greyscale image parameters

The Channel Format (Figure 2) indicates the preferred channel format for loading the image. This is ignored for 8-bit images. This also selects the texture bit depth of High Dynamic Resolution (HDR) images in Environment textures.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_149.png)       | Greyscale Image                                |
|                                   |                                                |
|                                   | ![](images/Greyscale_Image_Fig02_SE_v2026.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 2: The Import Settings shortcut

 

### Greyscale Image Parameters

Power- Controls image brightness. Lower values cause the image to appear darker. When used as a Bump map, this setting alters the bump height on the surface.

Color Space - Specifies the color space for the imported image.

Legacy [Gamma](javascript:void(0);) - Controls input image luminance, and tunes or color-corrects images if needed, however, this parameter is only used when the Color Space is set to Linear sRGB+Legacy.

Invert - Inverts the texture values.

Linear RGB Invert - Inverts the image after conversion to linear sRGB color space.

UV Transform - Positions, rotates, and scales the surface texture.

Projection - Accepts OctaneRender® Projection nodes. If nothing is connected to this input, the Image texture uses the surface\'s UV texture coordinates by default. This also changes the UV set if the original surface contains more than one UV set. For more details, see the [OctaneRender Projection Node](Projections.md) topic in this manual.

Border Mode U/V - Sets the behavior of the space around the image if it doesn\'t cover the entire geometry. Wrap Around is the default behavior, which repeats the image in the areas outside the image\'s coverage. If you set this parameter to White Color or Black Color, the area outside the image turns to white or black, respectively.
