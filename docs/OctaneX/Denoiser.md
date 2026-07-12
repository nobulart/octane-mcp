The Denoiser lets you render noise-free images with fewer kernel samples. The denoiser is not trained for the PMC and Info Channel kernels.There are two options for denoising type: Octane AI Denoiser and Open Image Denoise. 

To use the denoiser, enable this feature from the Camera Imager node under the Denoiser rollout (Figure 1). With the denoiser's tiling and multi-[GPU](javascript:void(0);) support, the OctaneRender® engine can denoise any resolution up to OctaneRender's maximum while consuming about 450 MB per device.

The denoiser is trained to denoise volumes and volume passes. Volumetric passes have very low frequency details, so don\'t use the Volumetric AI Denoiser with less than 1000 samples if you want to preserve details for final render quality that would resemble a 2K to 10K sample render of the scene.

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_446.png)       | Spectral AI Denoiser                   |
|                                   |                                        |
|                                   | ![](images/Denoiser_Fig01_SE_2024.jpg) |
+-----------------------------------+----------------------------------------+

Figure 1: Spectral AI Denoiser parameters

 

### Spectral AI Denoiser Parameters

Enable Denoising - Enables the Spectral AI Denoiser, which denoises some beauty passes - including the main beauty pass - and writes the outputs into separate render passes.

Denoiser - The denoiser method utilized for reducing noise. Thee are two options: The Octane AI Denoiser and the Open Image Denoise (OIDN from Nvidia) 

Denoise Volumes - If enabled, the Spectral AI Denoiser denoises volumes in the scene. Otherwise, volumes are not denoised by default.

Prefilter Auxillary AOVs - Only valid for the Open Image Denoise type. If enabled, the albedo and normal AOVs are internally pre-filtered before denoising the beauty AOV. Enabling this could improve the output quality if the albedo and normal AOVs are noisy. 

Denoise On Completion - If Enabled, beauty passes are denoised once at the end of a render. Disable this option if you\'re rendering with an interactive region.

Minimum Denoiser Samples - The minimum number of samples per pixel until the denoiser kicks in. This is only valid when Denoise On Completion is disabled.

Maximum Denoiser Interval - Maximum interval between denoiser runs in seconds. This is only valid when Denoise On Completion is disabled. The Denoiser Interval tells the denoiser to run when OctaneRender reaches this value. It is used for Interactive Render Region, which renders up to 1 million or until stopped. For this reason, OctaneRender provides the option to denoise periodically.

Blend - A value between 0.f - 1.f blends the original image into the denoiser output. 0.f results in a fully-denoised image, and 1.f results in an unaltered image. Intermediate values produce a blend of the denoised image and the original image.

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  To see the denoised result, enable the Denoiser in Camera Imager Settings, then select DeMain in the Render Viewport window. When using AOVs, make sure to select appropriate [Denoiser AOVs](DenoisedAOVs.md)
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
