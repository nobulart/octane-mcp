The OSL Baking Camera is a scriptable camera. You can create custom camera types for any purpose (such as [VR](javascript:void(0);) warping) with OSL ([Open Shader Language](javascript:void(0);)) scripts. It is a very flexible camera used to match the rendering to the existing footage. To learn about the generic OSL standard, read the [OSL Readme.](https://github.com/imageworks/OpenShadingLanguage/blob/master/README.md)

The OSL cameras work in conjunction with other OSL features like the OSL texture node. While the OSL camera\'s parameters are identical to the Standard camera, the OSL Baking camera contains a unique set of camera parameters used for controlling the baking process. These parameters are covered in more detail in the [Texture Baking](TextureBaking.md) topic under the Rendering section of this manual. To learn more about scripting within OctaneRender® using OSL, see the [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_377.png)       | OSL Baking Camera Parameters                     |
|                                   |                                                  |
|                                   | ![](images/OSL_Baking_Camera_Fig01_SE_v2020.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: The OSL Baking camera parameters.

 

### OSL Baking Camera Parameters

Baking Group ID - Specifies the group ID to bake. By default, all objects belong to the default baking group number 1.

UV Set - This determines the UV coordinates to use for baking.

##### Padding

Size - The number of pixels added to the UV map edges. The padding size is specified in pixels. The default padding size is set to 4 pixels, with 0 being the minimum and 16 being the maximum size.

Edge Noise Tolerance - Helps remove hot pixels appearing near the UV edges. Values close to 1 do not remove any hot pixels, while values near 0 attempts to remove them all.

##### Position

Continue if Transparent - If disabled, a transparent surface will terminate the path. If enabled, the ray will continue through the transparent surface.
