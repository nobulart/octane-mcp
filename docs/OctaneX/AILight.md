AI Light is a lighting algorithm implemented so that there is no difference in the resulting rendered image for unbiased rendering. It is designed to learn the scene that it is rendering and improve its sampling strategy over the course of rendering the image. However, GI clamp is a biased clamping method used to reduce fireflies, therefore it is possible the use of GI clamp can result in different brightnesses in parts of the image between the old light sampling and AI Light.

AI Light improves light sampling, especially in scenes that have many lights with localized distributions. As a learning system, AI Light improves as you render more samples. The learning is all done in the renderer - it is fully unbiased and tracks emissive points live and in real-time. When used with [Adaptive Sampling](javascript:void(0);), AI Light gets even better, since it learns that other lights become more important, as some pixels are no longer sampled.

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_362.png)       | Accessing AI Light Parameters           |
|                                   |                                         |
|                                   | ![](images/AI_Light_Fig01_SE_v2026.jpg) |
+-----------------------------------+-----------------------------------------+

Figure 1: AI Light controls are accessed from the Kernel settings\' Light section

 

### AI Light Parameters

AI Light - Enables AI lighting. This option is useful when the scene has complex lighting, such as a large scene with a lot of lights affecting a small local area in direct light coupled with the light emitters having a lot of polygons.

AI Light Update - Enables dynamic AI light update, which adaptively updates the light selection in direct light sampling, to help learn the current scene and where the lights are in that scene. For example, in cases where there is a wall occluding the light (the light has no effect in the given camera angle or position), AI Light Update understands that it does not need to sample this light.

+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                         |
|                                                                                                                                                                                                                              |
| Scenes rendered using versions 3.x.x and earlier will not have AI light attributes. These attributes will need to be explicitly set in the Kernel settings when the scenes are opened in Octane by enabling AI Light update. |
+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
