The Mask with Cryptomatte Output AOV node is used to mask out parts of a composite using a cryptomatte generated as a Render AOV (figure 1).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_562.png)       | Mask With Cryptomatte                               |
|                                   |                                                     |
|                                   | ![](images/Mask_With_Cyrptomatte_Fig01_SE_2024.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: The Mask with Cryptomatte Output AOV node used to mask out the Octane logo a composite node tree

### Mask With Cryptomatte Parameters

Enabled - Determines whether Mask with Cryptomatte is active or not.

Type - Determines the type of Crypomatte Render AOV from which to extract the mattes.

Mattes - Lists the names of the objects selected as mattes. A \* is a wildcard that matches any sequence of characters and a - at the start of a line excludes any mattes by that name.

Affect Occlusion Only - If enabled, scales only the alpha channel to control how much the image blocks light from neneath it without changing how much additional light the image contributes. If disabled, scales the (premultiplied) RGB channels as well, to control how much additional light the image contributes. This should be disabled for a normal SDR image masking scenario where the image is thought of as a colored sheet with an alpha mask, and enabled for an emissive/HDR image where occlusion (alpha) and emission (RGB) are considered separately.
