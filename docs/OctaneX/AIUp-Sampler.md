OctaneRender® includes a built-in AI upsampler in the Camera Imager. When specifying an Upsampler Mode, the AI upsampler performs a faster render at a lower resolution, then upscales to the final resolution. The AI Upsampler also has progressive and one-stop upsampling modes, similar to the AI denoiser.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_501.png)       | ai upsampler parameters                       |
|                                   |                                               |
|                                   | ![](images/AI_Up_Sampler_Fig01_SE_v_2024.png) |
+-----------------------------------+-----------------------------------------------+

Figure 1: Accessing Upsampler parameters in the Node Inspector

 

### Upsampler Parameters

Upsampler Mode - Selects the upsampler mode for rendering. The image renders at a lower resolution divided by the sampling mode, then it upscales to the final resolution.

Enable AI Upsampling - When you have an Upsampler Mode selection made and you have this option enabled, the render scales using AI upsampling. Otherwise, scaling is done using traditional methods.

Upsample On Completion - Beauty passes upsample once at the end of a render.

Min. Upsampler Samples - The minimum number of samples per pixel until the upsampler activates. This parameter doesn\'t apply if you select No Upsampling in Upsampler Mode.
