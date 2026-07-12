Deep render AOVs work with [Deep Image](javascript:void(0);) rendering in the Direct Lighting, Path Tracing, and Photon Tracing kernels. When enabled, all render passes enabled in the Render AOVs node are written to the deep pixel channels. By default, only the beauty AOV is written.

  ---------------------------------------------------------------------------------------
  NOTE: Enabling this feature can use a lot of VRAM if you are rendering a large image.
  ---------------------------------------------------------------------------------------

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_389.png)       | Deep Render AOVs in the Kernel Node      |
|                                   |                                          |
|                                   | ![](images/Deep_AOVs_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------+

Figure 1. Deep Render AOVs are enabled through the Kernel node
