Rendering animations can be accomplished using the [Batch Rendering](javascript:void(0);) script found in the Script menu (figure 1).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_443.png)       | Batch Rendering                                     |
|                                   |                                                     |
|                                   | ![](images/Rendering_Animations_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: Animation settings in the Batch Rendering window

Additionally, the Animation Settings node controls the shutter interval for applying motion blur in a scene.The value is relative to the frame time, which you set in the time slider from the FPS option.

The Animation Settings parameters are accessible from the Node Inspector window without adding and connecting a specific Animation Settings node to the scene.

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_444.png)       | Animation Settings                   |
|                                   |                                      |
|                                   | ![](images/RenderingAnimations1.jpg) |
+-----------------------------------+--------------------------------------+

Figure 2: The Animation Settings button

 

### Animation Settings Parameters

Shutter Alignment - Specifies how the shutter interval aligns to the current time, which determines when the camera shutter is triggered. The options are Before, Symmetrical, or After, and they apply to each frame thereafter relative to the given frame rate.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_445.png)       | Shutter Alignment                                     |
|                                   |                                                       |
|                                   | ![](images/animationsettings_fig2_SEv4-0_941x600.png) |
+-----------------------------------+-------------------------------------------------------+

Figure 3: Illustrating the After, Before, and Symmetrical Shutter Alignment

Shutter Time - The shutter time percentage relative to the duration of a single frame, which controls how much time the shutter stays open. You can set this parameter to any value above 100%.

Subframe Start/Subframe End - Specifies the approach, in terms of proportion (%) to simulate the camera's shutter speed for that particular frame. OctaneRender uses Subframe Start and End percentages to render only a portion of a particular frame. If the scene has a lot of motion blur, OctaneRender® uses these parameters to render a piece of that motion blur. The default Start and End values of 0% and 100%, respectively, render the whole frame.

+---------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                    |
|                                                                                                         |
| [Motion Blur](javascript:void(0);) with [Displacement](javascript:void(0);) is currently not supported. |
+---------------------------------------------------------------------------------------------------------+
