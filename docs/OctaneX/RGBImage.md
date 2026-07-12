RGB Image textures connect an external image file to any material parameters that accept a texture map (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_155.png)       | RGB Image                                 |
|                                   |                                           |
|                                   | ![](images/RGB_Image_Fig01a_SE_v2022.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The RGB Image node is importing a PNG image into a [Diffuse material](javascript:void(0);)\'s [Diffuse](javascript:void(0);) pin

The RGB Image texture converts all images to three-channel images, including greyscale images. To use memory resources efficiently, use the RGB Image texture for color inputs. For greyscale channels such as Bump, use the Greyscale Image texture.

Use the Import settings button (Figure 2) to indicate the preferred channel format for loading the image. This is ignored for 8-bit images. You can also use this for selecting the texture bit-depth of High Dynamic Resolution images in Environment textures.

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_156.png)       | RGB Image                                |
|                                   |                                          |
|                                   | ![](images/RGB_Image_Fig02_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------+

Figure 2: The import settings shortcut

 

### RGB Image Parameters

Power - Adjusts the scene brightness. We recommend leaving this set to 1 and use the Power setting to brighten or dim the lighting.

Color Space - Determines the color space for the HDR image.

Legacy [Gamma](javascript:void(0);) - Controls the [HDRI](javascript:void(0);) file\'s luminance value when the Color Space is set to Linear sRGB + Legacy Gamma.

Invert - Inverts the color values of the HDRI Image.

Linear sRGB Invert - Inverts the HDRI after conversion to linear sRGB color space, not before.

UV Transform - This controls how OctaneRender® maps textures by applying a matrix texture coordinate. To adjust the HDRI image rotation for lighting a scene, we recommend adjusting the Projection settings instead.

Projection - Allows the user to specify mapping modes (or texture projections) to supplement texture transforms. The Spherical, Cylindrical, Flat, Box, and Perspective mapping modes can manipulate the UV transforms and world space coordinates used in Image textures, Procedural textures, and Camera mapping. For Environment maps, the Spherical projection mode is often used. To make it easier to rotate the texture, set the Sphere Transformation to 3D Rotation and adjust the angle\'s settings.

Border Mode U/V - Sets the behavior of the space around the image if it doesn\'t cover the entire geometry. Wrap Around is the default behavior, which repeats the image in the areas outside the image\'s coverage. If you set this parameter to White Color or Black Color, the area outside the image turns to white or black, respectively.
