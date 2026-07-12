OctaneRender® is a GPU-based render engine, and it is important to manage the GPUs in the system used for rendering. This is done from the Devices tab (Figure 1). Under this tab, the GPUs supported by your computer appear with checkboxes in a list. Unsupported GPUs are not shown.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_12.png)        | Devices                                         |
|                                   |                                                 |
|                                   | ![](images/Devices_Settings_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: Devices tab

The Devices tab displays the following:

- CUDA Driver - This shows the current CUDA® driver and runtime versions.
- Render - Select GPUs to use for rendering if more than one GPU is installed.
- Use Priority - This shows whether the device will use the priority indicated at the Render Viewport's Render Priority setting. The Use Priority option throttles down rendering on one or more GPUs to improve system responsiveness, especially when rendering on a GPU used for the display.
- Image -If enabled, image tonemapping will will be active for the specified GPU.
- Denoise - Enables the specific GPU to be used for denoising.
- Device Info - Shows the selected device\'s specifications.
- Device Memory Usage - This shows how the video card memory is allocated based on the current scene\'s geometry, textures, render target, etc.
- GPU Headroom - Determines the amount of GPU memory to leave free on each graphics card when storing image textures or geometry data. VRAM is faster than RAM, therefore GPU Head Room tends to be set to a minimal level since it is practical to have the maximum amount of texture and geometry data fitted into VRAM.
