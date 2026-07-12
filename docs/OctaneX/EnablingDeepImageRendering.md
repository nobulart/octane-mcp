Deep image parameters can be accessed from the Deep Image rollout in the Kernel parameters (figure 1)

+-----------------------------------+----------------------------------------------------------+
| ![](images/NewItem_390.png)       | Deep IMage Parameters                                    |
|                                   |                                                          |
|                                   | ![](images/EnablingDeepImageRendering_SEv2018-1-RC6.png) |
+-----------------------------------+----------------------------------------------------------+

Figure 1: [Deep Image](javascript:void(0);) checkbox

 

### Deep Image Parameters

Deep Image - Enables deep image rendering.

Deep Render AOVs - Includes render AOVs for deep image pixels.

Max. Depth Samples - Specifies an upper limit for the number of deep samples stored per pixel.

Depth tolerance - Specifies a merge tolerance - i.e., when two samples have a relative depth difference within the depth tolerance, they merge.

For a typical scene, the [GPU](javascript:void(0);) renders thousands of samples per pixel. However, VRAM is limited, so it\'s necessary to manage the number of samples stored with the Deep [Render Passes](javascript:void(0);) and Max. Depth Samples parameters.

 

#### Deep Bin Distribution Calculation

The maximum number of samples per deep pixel is 32, but we don\'t throw away all the other samples. When we start rendering, we collect a number of seed samples, which is a multiple of Max. Depth Samples. With these seed samples, we calculate a deep bin distribution, which is a good set of bins characterizing the various depth depths of the pixel\'s samples. There is an upper limit of 32 bins, and the bins are non-overlapping. When we render thousands of samples, each sample that overlaps with a bin is accumulated into that bin. Until this distribution is created, you can\'t save the render result, and the Deep Image option in the Save Image dropdown is disabled.

 

#### Limitations

Using deep bins is just an approximation, and there are limitations to this approach. When rendering deep volumes (meaning a large Z extend), there might not be enough bins to represent this volume all the way to the end, which cuts the volume off in the back. You can see this if you display the deep pixels as a point cloud in Nuke®. You can still use this volume for compositing, but up to where the first pixel is cut off. If there aren\'t enough bins for all visible surfaces, some surfaces can be invisible in some pixels. This situation is more problematic, and the best option is to re-render the scene with a bigger upper-limit for the deep samples.

After creating the deep bin distribution, you need to upload it onto the devices for the whole render film. Even with tiled rendering, deep image rendering uses a lot of VRAM, so don\'t be surprised if the devices fail when starting the render. The amount of buffers required on the device can be too big for the configuration - check the log to make sure. The only thing you can do here is reduce the Max. Depth Samples parameter or the resolution.

Here is an example project and a deep OpenEXR file rendered with it: [](https://render.otoy.com/downloads/41/1e/b5/ca/deep-image-example.zip) [deep-image-example.zip](https://render.otoy.com/downloads/41/1e/b5/ca/deep-image-example.zip)
