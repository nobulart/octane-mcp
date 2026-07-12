This script provides options for creating a daylight-based animation sequence (Figure 1). It requires that a Daylight Environment node is connected to the Render Target node.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_81.png)        | Daylight Animation                                |
|                                   |                                                   |
|                                   | ![](images/Daylight_Animation_Fig01_SE_v2020.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: The Daylight Animation script settings.

 

### Daylight Animation Parameters

Start Hour - Specifies the hour to start the animation.

End Hour - Specifies the hour to end the animation.

Duration - Determines how long it will take to go from the Start Hour to the End Hour.

Framerate - Determines the animation frame rate.

Frames - Specifies the total number of frames for the animation sequence. This number is connected to the Duration parameter.

Samples/px - Determines the number of Kernel samples.

Output - The path to render out the animation sequence.

Start File Numbering - Specifies the starting number for the frame numbering.

Skip Existing Image Files - Specifies whether to overwrite existing image files.
