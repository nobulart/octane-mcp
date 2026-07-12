You can manage the default Image Import settings under File \> Preferences \> Image Import.

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_20.png)        | image import                                         |
|                                   |                                                      |
|                                   | ![](images/Image_Import_Settings_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 1: Image Import parameters

### Image Import Preferences

HDR Texture Import Type - Specifies how HDR images are imported into the native Image texture nodes. The best choice for the bit-depth is to match the channel size used for rendering. If you use a 16-bit channel size is used for rendering, OctaneRender® imports HDR images as 16-Bit Float by default. This saves RAM used for HDR textures. OctaneRender can also import HDR textures as 32-Bit Float. The Automatic option uses the file\'s channel size.

IES Scaling - Determines how to normalize data from an IES light profile file.

Bake PNG Gamma on Loading - If the PNG file has a Gamma value, this converts the image to display a Gamma of 2.2 when loading. If disabled, the image does not receive any Gamma correction.
