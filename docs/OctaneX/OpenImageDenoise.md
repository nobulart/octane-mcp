The Open Image Denoise Output AOV node is an AI-powered denoising feature that leverages the Intel Open Image denouise technology. It can be used to denoise all or portions of a composite node tree (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_572.png)       | Open Image Denoise                               |
|                                   |                                                  |
|                                   | ![](images/Open_Image_Denoise_Fig01_SE_2024.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: The Open Image Denoise Output AOV node used to remove noise from a composite node tree

### Open Image Denoise Parameters

Enabled - Determines whether the effect is active or not.

Albedo - (Optional) The input contains the albedo data. Ideally, the albedo obtained from the first diffuse bounce. This data is recorded in the Denoise Albedo Render AOV. 

Normal - (Optional) The input contains the shading normal per pixel. Ideally, the normal obtained from the first diffuse bounce. This data is recorded in the Denoise Normal Render AOV.

Prefilter Auxillary Inputs - Internally pre-filters the albedo and normal inputs before denoising the background layer. Enabling this parameter could improve the output quality if the albedo and normal inputs are noisy, but it will also increase the time required to complete the denoising process.
