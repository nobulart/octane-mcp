The Image Tiles node allows you to define UDIM-like offsets in OctaneRender. Also known as U-Dimension, the primary reason for UDIMs is image texture resolution, where you can have specific grids with close ups of specific parts of an object, such as an eye or engine in the same overall UV and texture set. By creating multiple UDIMs tiles in the grid, you can specifically tailor image maps to a needed use. The Image Tiles node will reference UDIMs as a sequentially numbered image sequence, making working with said maps in applications like Nuke or After Effects a very simple process, since these maps are treated like typical rendered frames in these applications. 

There are two different naming syntaxes for the tiled textures:

- name\_%u\_%v.ext  (U is the row and V is the column number --- they can start from 1.)
- name\_%i.ext (i is an index of images and should start at 1001.)  Note that file naming is depending to row size.

After you select the Image Tiles node, go to the Node Inspector and click on the Load Images icon to select and load images into the grid (figure 1).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_150.png)       | Loading Image Tiles                                |
|                                   |                                                    |
|                                   | ![](images/Image_Tiles_Texture_Fig01_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: Clicking the Load Images icon from the Image Titles parameters

From the Tiles window, adjust the grid\'s length and width from the Grid Size parameter, then press the Browse button to load the UDIM files (figure2).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_151.png)       | Image Tiles                               |
|                                   |                                           |
|                                   | ![](images/Image_Tile_Fig02_SE_v2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: The Image Tiles window

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_153.png)       | Scene Graph                                         |
|                                   |                                                     |
|                                   | ![](images/ImageTilesTexture_Fig04_SEv4-00-xb4.png) |
+-----------------------------------+-----------------------------------------------------+

Figure 3: A basic scene graph using Image Tiles texture

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_154.png)       | Image Tiles Texture                                |
|                                   |                                                    |
|                                   | ![](images/Image_Tiles_Texture_Fig04_SE_v2022.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 4: Image Tiles texture with three tiled images applied to the [Diffuse](javascript:void(0);) input on a [Glossy material](javascript:void(0);)

 

### Image Tiles Parameters

Power- Controls image brightness. Lower values cause the image to appear darker. When used as a Bump map, this setting alters the bump height on the surface.

Color Space - Specifies the color space for the imported image.

Legacy [Gamma](javascript:void(0);) - Controls input image luminance, and tunes or color-corrects images if needed, however, this parameter is only used when the Color Space is set to Linear sRGB+Legacy.

Invert - Inverts the texture values.

Linear RGB Invert - Inverts the image after conversion to linear sRGB color space.

Gamma - Controls the input image luminance, and it also tunes or color-corrects the image.

Invert - Inverts the texture values.

UV Transform - Positions, rotates, and scales the surface texture.

Projection - Accepts OctaneRender®Projection nodes. If nothing is connected to this input, the Image texture uses the surface\'s UV texture coordinates by default. This also changes the UV set if the original surface contains more than one UV set. For more details, see the [OctaneRender Projection Node](Projections.md) topic in this manual.

Empty Tile Color - Specifies the color to use when a tile is empty.
