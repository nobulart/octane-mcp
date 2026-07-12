The camera Imager settings provide useful parameters for post-rendering adjustments. To adjust the camera imager settings, select the Imager node in the Graph Editor, or select the Current Imager icon in the Node Inspector (Figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_368.png)       | Node Inspector toolbar                    |
|                                   |                                           |
|                                   | ![](images/CameraImagerSettingsFig01.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Camera Imager button on the Node Inspector toolbar

### Camera Imager Parameters

Exposure - Controls the scene exposure. Smaller values create a dark scene, while higher values create a bright scene. Exposure has no effect on any of the render layer passes.

Hot Pixel Removal - Removes bright pixels (fireflies) during the rendering process. While many of the pixels can disappear if the render progresses, Hot Pixel Removal removes bright pixels at a much lower sample-per-pixel.

Vignetting - Adjusting this parameter increases the amount of darkening in the corners of the render. Used sparingly, it can increase the render\'s realism. Vignetting is not applied to any of the beauty passes except the main pass.

White Point - Specifies the color for adjusting the tint to produce and simulate the relative temperature cast throughout the image by different light sources. The white point is white by default, acting as a white balance to achieve the most accurate colors possible.

Saturation - Adjusts the amount of color saturation in the render.

Disable Partial Alpha - Makes pixels that are semi-transparent (Alpha \> 0) into fully opaque pixels.

Dithering - Adds random noise, which removes banding in very clean images.

Minimum Display Samples - The minimum amount of samples calculated before the image displays. This feature can reduce noise when navigating, and is useful for real-time walkthroughs. When using multiple GPUs, we recommend setting this value as a multiple of the number of available GPUs for rendering. If you're rendering with four GPUs, set this value to 4 or 8.

Maximum Image Interval - Maximum interval between image operations in seconds.

#### OCIO

OCIO View - The OCIO view to use when displaying in the render viewport. See the [Color Management](TheColorManagementSettings.md) section for more information. 

OCIO Look - The OCIO look to apply when displaying in the render viewport, if using an OCIO view.

Force [Tone Mapping](javascript:void(0);) - Before applying any OCIO looks, this toggles whether to apply OctaneRender\'s built-in tone mapping when using an OCIO view.

#### Tone Mapping

ACES Tone Mapping - Uses the ACES 1.2 RRT+sRGB. If this option is enabled, all other tone mapping settings will be ignored.

Highlight Compression - Reduces burned out highlights by compressing them and reducing their contrast.

Clip To White - When the sun is too bright, it can create multicolored reflections. Increasing this value changes the colors to white. This is also applicable to all sources of light. Saturated parts of the render can be pushed towards pure white with this option. This helps avoid large patches of fully saturated colors caused by over-bright light sources such as very bright colored emitters or reflected sunlight off colored surfaces.

Order - This defines the order that the Response Curve, [Gamma](javascript:void(0);), and Custom LUT is applied on the scene. 3D LUTs are defined for sRGB input values (you will want to apply the Custom LUT last), but there might be 3D look-up tables for linear input data, in which case you might want to apply the Custom LUT first.

Response Curve - Selects measured camera response curves. OctaneRender® also has response curves that reproduces the rendering neutrally on a normal display. The sRGB, Gamma 2.2, and Gamma 1.8 options are applicable for most displays that use sRGB or apply a gamma of 2.2 or 1.8.

+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                                                                    |
|                                                                                                                                                                                                                                                                         |
| The most common response curve is sRGB, which is the Camera Imager node\'s default setting. Since this option did not exist in earlier versions of OctaneRender®, any scene with an sRGB response curve in the Imager settings reverts to Linear/Off in older versions. |
+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

For examples of all the camera responses, see the Appendix topic in this manual on Camera Response Curve.

Neutral Response - If enabled, the camera response curve doesn\'t tint the render result. In Figure 3, the left image is the material ball rendered with no response curve and Gamma set to 2.2. The center image uses the Agfacolor HDC 200 curve and a Gamma of 1. The right image shows the same curve with Neutral Response enabled.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_370.png)       | Neutral Response Curve                    |
|                                   |                                           |
|                                   | ![](images/CameraImagerSettingsFig03.png) |
+-----------------------------------+-------------------------------------------+

Figure 3: Adjusting the Neutral Response curve

Gamma - Adjusts the render gamma and controls the image\'s overall brightness. Images that are not properly corrected can look bleached out or too dark. Varying the amount of Gamma correction changes the brightness and the ratios of red to green to blue.

Custom LUT - Specify any standard or user-defined 3D Lookup Table (.cube file) for OctaneRender® to map one color space to another. If this attribute is set, the custom LUT is applied in the order specified through the Order attribute.

#### Denoiser

Enable Denoising - Enables the Spectral AI Denoiser, which denoises some beauty passes - including the main beauty pass - and writes the outputs into separate render passes.

Denoiser - The denoiser method utilized for reducing noise. Thee are two options: The Octane AI Denoiser and the Open Image Denoise (OIDN from Nvidia) 

Denoise Volumes - If enabled, the Spectral AI Denoiser denoises volumes in the scene. Otherwise, volumes are not denoised by default.

Denoise On Completion - If Enabled, beauty passes are denoised once at the end of a render. Disable this option if you\'re rendering with an interactive region.

Minimum Denoiser Samples - The minimum number of samples per pixel until the denoiser kicks in. This is only valid when Denoise On Completion is disabled.

Maximum Denoiser Interval - Maximum interval between denoiser runs in seconds. This is only valid when Denoise On Completion is disabled. The Denoiser Interval tells the denoiser to run when OctaneRender® reaches this value. It is used for Interactive Render Region, which renders up to 1 million or until stopped. For this reason, OctaneRender® provides the option to denoise periodically.

Blend - A value between 0.f - 1.f blends the original image into the denoiser output. 0.f results in a fully-denoised image, and 1.f results in an unaltered image. Intermediate values produce a blend of the denoised image and the original image.

#### Upsampler

Upsampler Mode - Selects the upsampler mode for rendering. The image renders at a lower resolution divided by the sampling mode, then it upscales to the final resolution.

Enable AI Upsampling - When you have an Upsampler Mode selection made and you have this option enabled, the render scales using AI upsampling. Otherwise, scaling is done using traditional methods.

Upsample On Completion - Beauty passes upsample once at the end of a render.

Min. Upsampler Samples - The minimum number of samples per pixel until the upsampler activates. This parameter doesn\'t apply if you select No Upsampling in Upsampler Mode.
