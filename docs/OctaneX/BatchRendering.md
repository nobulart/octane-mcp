In OctaneRender®, each frame of an animated scene needs to be rendered and then saved on disk for later compositing. This process will be tedious enough when done manually for every frame, so this is where batch rendering becomes useful.

The batch rendering script is one of those readily available under the Script menu. When invoked, it requires at least one Render Target present in the current scene, but if there are more Render Targets, the script provides the option to include specific Render Targets and a choice of image formats for each Render Target\'s output, respectively. The script detects the Render Targets and sorts them in alphanumerical order.

The batch rendering script can do the following:

- Detect Render Targets nested in a Nodegraph.
- Selects the Render Targets to render in the batch.
- Assigns an index to each Render Target and uses it in the output name (instead of the render time), which prevents overwrites.
- Specifies the output format.
- Supports saving PNG and [EXR](javascript:void(0);) files and allows scrolling.
- Allows of both the main beauty and the denoised main passes.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_80.png)        | Batch Rendering                                |
|                                   |                                                |
|                                   | ![](images/Batch_Rendering_Fig01_SE_v2023.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: [Batch Rendering](javascript:void(0);) parameters

### Batch Render Parameters

Render Target - Specifies the Render Targets to render.

Format - Choose amongst a variety of PNG and EXR formats.

Color Space - The output color space which can be a built-in color space or an OCIO color space.

OCIO Look - The OCIO look to apply, if using an OCIO color space.

[Tone Mapping](javascript:void(0);) - Determines whether to apply Octane\'s built-in ton emapping when saving in a color space other than sRGB. This tone mapping is applied prior to any OCIO look.

Framerate - Sets the frame rate for animated scenes.

Start Frame - Selects the first frame of the render job.

End Frame - Selects the last frame of the render job.

Sub Frame - Specifies the number of subframe to render.

File Numbering - Determines the starting number attached to each rendered frame\'s file name.

Override Samples - Each Render Target has its maximum number of samples. This option makes it easier to override the maximum samples originally set in the kernel for that batch.

Filename Template - Determines the parameters included in naming the rendered files. The parameters are:

- %i render target index
- %n node name
- %e extension (file format)
- %t timestamp
- %f file numbering (handy for indicating frames)
- %p render pass name

For example, batch rendering an [Alembic](javascript:void(0);) scene with 80 frames and three Render Targets, a typical filename template would be %n\_%f\_%p.%e, which will save rendered images as: \<render target node name\>\_\<file numbering\>\_\<render pass name\>.\<file format extension\>.

DL 10_1_Beauty.pngDL 10_2_Beauty.png\...DL 10_80_Beauty.pngIC WF_1_Beauty.pngIC WF_2_Beauty.png\...IC WF_80_Beauty.pngPMC 10_1_Beauty.pngPMC 10_2_Beauty.png\...PMC 10_80_Beauty.pngPT 10_1_Beauty.pngPT 10_2_Beauty.png\...PT 10_80_Beauty.png

Output Folder - This invokes the operating system's standard file and folder dialog to allow users to create or specify a folder to store where the rendered images resulting from the batch render will be stored. If the oOutput folder or the filename is left blank, OctaneRender® will still renders everything, but it won\'t not save the images. Other animation scripts will do the same thing. This way, you can test render the scene without having to save it.

Skip Already Existing File - Skips the existing file.

Save All Enabled Passes - Save enabled passes and/or layered EXR when the passes are saved in EXR format.

Save Denoised Main Pass If Available - Saves the denoised main pass, if you made one.

Save Layered EXR - Saves your EXR file as a layered EXR.

Premultiplied Alpha (only when saved as EXR) - Determines whether to multiply or premultiply the rendered images.

EXR Compression Type - Choose the type of compression to use on the EXR file.

Save Additional [Deep Image](javascript:void(0);) - Includes and saves additional deep image data.

TIFF Compression Type - Determines the compression type when saving to TIFF format.

JPEG Quality - Determines the quality level when saving to JPEG format.
