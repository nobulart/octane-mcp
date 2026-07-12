The OctaneRender® Photoshop Compositing Extension provides tools for compositing OctaneRender® render passes and support for loading multilayer OpenEXR file format (16- and 32-bits). It can be obtained [here](https://exchange.adobe.com/addons/products/13589) on the Adobe Add-Ons website, but it is also included in every new OctaneRender® Standalone release post.

 

### Installing The Extension

- - Photoshop® CS6 to CC 2014: If you\'ve downloaded the extension bundle, you can install it with [Adobe Extension Manager CC](https://www.adobe.com/exchange/em_download/), which makes sure all the contained plugins and additional files are properly set up within Photoshop®.
  - Photoshop® CC 2015: Add the extension to Photoshop® from the [Adobe Add-ons website](https://exchange.adobe.com/addons). Alternatively, if you have downloaded the extension bundle from the forums, Note that the extension manager [has been discontinued by Adobe for CC 2015 applications](https://www.adobeexchange.com/resources/27), so you may use [ZXPInstaller](http://zxpinstaller.com/) as an alternative.

Once you install the extension, is installed you will find new entries for each plugin by clicking on About Plug-In within the Help \> About Plug-In menu on Windows®, or Photoshop CC \> About Plug-In on macOS®.

![](images/OctaneRenderCompositingExtension1_376x267.png)

Figure 1: About Plug-In options

 

Also, the Automate option under the File menu has a couple options to choose from.

![](images/OctaneRenderCompositingExtension2_467x555.png)

Figure 2: Automate options from the File menu

 

### The OTOY® EXR Plugin

This plugin provides support for loading multi-layer OpenEXR files (16- and 32-bit) into Photoshop®. When installed, it overrides the default [EXR](javascript:void(0);) Photoshop® loader, which supports just single-layer EXR files and loading them by clicking on File \> Open. After loading the file, the plugin undos any pre-multiplication to your data if it\'s been exported using pre-multiplied alpha, as well as adjust the gamma level in case the data is not in linear colorspace.

![](images/OctaneRenderCompositingExtension3_277x228.png)

Figure 3: EXR Import window

+-----------------------------------------------------------------------+
| NOTE                                                                  |
|                                                                       |
| The plugin does not support saving into the OpenEXR files.            |
+-----------------------------------------------------------------------+

### Loading the OctaneRender® Compositing Project Plugin

This is the central part of the extension and allows you to load an OctaneRender Compositing Project (\*.ocprj) file into Photoshop®. To create such a project file, you have to enable certain options in the [Render Passes](javascript:void(0);) Export window.

![](images/OctaneRenderCompositingExtension4_450x670.png)

Figure 4: Generate Compositing Project File option

 

Whether you\'ve exported multi-layer EXR or discrete files, you can browse your compositing project file by clicking on File \> Automate \> Load OctaneRender Compositing Project\.... The plugin loads all your project files in a single document and undos the data if necessary, setting up all layer blending and grouping as needed. Once loaded, you may start compositing your image, then save this document as a PSD file or export it in any other format you wish.

 

### Set Up OctaneRender® Render Layers Plugin

This plugin arranges render passes exported from OctaneRender® to display as layers in Photoshop® using the right layer grouping and blending, achieving the same image composition as it would be displayed by OctaneRender®. You can use this regardless if you loaded your document from a compositing project, or created it by other means. Once the render passes are loaded as layers into a Photoshop® project, click on File \> Automate \> Setup OctaneRender [Render Layers](javascript:void(0);).

The plugin goes through all of your document layers, sets the proper layer order and blending, and creates the required layer groups. Layers recognized as render passes are highlighted in green. Layers that are not render passes are disabled and marked in yellow as a warning.

 

### Material Render Passes

Once you\'ve loaded your material render passes, they may look something like this:

![](images/OctaneRenderCompositingExtension5_366x229.png)

Figure 5: [Material](javascript:void(0);) render passes

 

The beauty pass is shown first, hiding the rest of layers. After running the plugin, the layers are separated into foreground and environment. The transparency is removed from the foreground layers and applied to the foreground group as an alpha mask. Blending is applied according to each render pass setting in OctaneRender®.

![](images/OctaneRenderCompositingExtension6_397x248.png)

Figure 6: Render passes with blending applied

 

### Lighting Render Passes

Once you\'ve loaded your lighting render passes, they may look something like this:

![](images/OctaneRenderCompositingExtension7_392x245.png)

Figure 7: Lighting render passes

After running the plugin, the layers are grouped and the blending is set to Linear Dodge (Add), resulting in the right blending.

![](images/OctaneRenderCompositingExtension8_451x281.png)

Figure 8: Lighting render passes with grouping and blending applied

 

### Render Layers Render Passes

Once you\'ve loaded your render layers, they may look something like this:

![](images/OctaneRenderCompositingExtension10_444x277.png)

Figure 9: Render layers render passes

After running the plugin, render pass layers are grouped and the right blending is set. The beauty layer, opposite to the previous render pass types, is enabled. An additional background placeholder layer is also created if you want to provide a background image.

![](images/OctaneRenderCompositingExtension9_450x281.png)

Figure 10: Render layer render passes with grouping and blending

+------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                       |
|                                                                                                                                                            |
| The shadows pass layer is enabled if no black or colored shadows are not present. If just one of them is present, then the shadows pass layer is disabled. |
|                                                                                                                                                            |
| If you are using an environment you should enable \'Alpha channel\' in your kernel settings.                                                               |
+------------------------------------------------------------------------------------------------------------------------------------------------------------+

### Known Issues

When exporting beauty passes, do not use the Raw flag, as the extension blending does not take it into account.

In Photoshop® CS6, if there are any render layer passes present, the layer arrangement will fail.
