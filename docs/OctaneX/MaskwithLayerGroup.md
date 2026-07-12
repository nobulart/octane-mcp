The Mask with Layer Group Output AOV node is used to mask out parts of a composite using other Output AOV nodes (figure 1).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_564.png)       | Mask With Layer Group                               |
|                                   |                                                     |
|                                   | ![](images/Mask_With_Layer_Group_Fig01_SE_2024.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: The Mask with Layer Group Output AOV node used to mask out the luminance vlaues of the Diffuse Render AOV

### Mask With Layer Group Parameters

Enabled - Determines whether Mask with Layer Group is active or not.

Source - Determines which values from each pixel will be used as a mask.

Affect Occlusion Only - If enabled, scales only the alpha channel to control how much the image blocks light from neneath it without changing how much additional light the image contributes. If disabled, scales the (premultiplied) RGB channels as well, to control how much additional light the image contributes. This should be disabled for a normal SDR image masking scenario where the image is thought of as a colored sheet with an alpha mask, and enabled for an emissive/HDR image where occlusion (alpha) and emission (RGB) are considered separately. 

Layer (s) - Specifies the layers to be used as masks. Multiple layers can be added by clicking on the Add Layer button.
