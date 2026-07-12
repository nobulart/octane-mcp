OctaneRender® implements animated image textures by animating the file name attribute in any one of the texture nodes that import external texture maps. To set it up, click the Animation button in the Node Inspector.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_157.png)       | Importing Image Sequence                              |
|                                   |                                                       |
|                                   | ![](images/Animated_Image_Texture_Fig01_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: Animation button

 

This opens the Assign New Texture Animation window. From there, you can add the sequence of image files by clicking on the Add Files button.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_158.png)       | Importing Image Sequence                              |
|                                   |                                                       |
|                                   | ![](images/Animated_Image_Texture_Fig02_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 2: Assign New Texture Animation window

 

### Texture Animation Parameters

Animation Mode - Selects how you want the animation file to run. The following modes are available:

- - Once - Runs through the sequence once.
  - Loop - Runs through the sequence and repeats it indefinitely.
  - Ping-Pong - Runs through the sequence from beginning to end, then from the end back to the beginning, and repeats the sequence indefinitely.

Starting Frame - Set the frame number to start on for the animation.

Frames Per File - Sets the number of frames to display each image of the sequence. The Framerate is defined in the time slider of the Render viewport - i.e., it comes from the project. It\'s displayed in the dialog just for convenience.

Total Frames - Adjusts the total number of frames to play the animation sequence.

When you save a project as a package, all of the specified images in the sequence are stored in the package. After opening this package, you can still remove an image from the sequence and change its order, but you cannot add new files from the file system. This is a limitation of the animated file name attribution - this avoids having files coming from multiple packages or from the file system in the same sequence.
