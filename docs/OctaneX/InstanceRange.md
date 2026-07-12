The Instance Range texture node functions in a similar way to the Instance Color texture node. The Instance Range texture holds a greyscale color with the Maximum ID range of 0 to whatever figure you enter in this parameter, and OctaneRender® prepares this range to map it to geometric instance IDs.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_222.png)       | Instance Range                              |
|                                   |                                             |
|                                   | ![](images/instance_range_Fig1_536x144.png) |
+-----------------------------------+---------------------------------------------+

Figure 1: Parameters of the Instance Range texture node

Just as a [Lua](javascript:void(0);) script or any of the OctaneRender plug-ins are able to generate instances of an object, these same processes can also assign an ID to each generated instance, which results in a grid of instance IDs. You can then assign colors to each instance ID via Texture (in this case with an image in the Instance Color texture), and match the IDs with pixels of the image, starting at the bottom-left and moving up to the top-right. For the example below, there are 10x10 instances that a Lua script assigns IDs to each instance, generating 100 IDs. To map the range, the Maximum ID attribute must match the number of generated IDs - 100 in this case.

+-----------------------------------+-------------------------------------+
| ![](images/NewItem_223.png)       | 10x10 Grid Instanced Cubes          |
|                                   |                                     |
|                                   | ![](images/instance_range_Fig2.png) |
+-----------------------------------+-------------------------------------+

Figure 1: A 10x10 grid of greyscale colors in an Instance Range

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_224.png)       | Nodegraph Layout                            |
|                                   |                                             |
|                                   | ![](images/instance_range_Fig3_489x395.png) |
+-----------------------------------+---------------------------------------------+

Figure 2: Instance Range node in the Nodegraph

 

You can use other mapping textures, such as the Gradient Map texture, in conjunction with the Instance Range to create some interesting variations.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_225.png)       | Gradient Map                                  |
|                                   |                                               |
|                                   | ![](images/Instance_Range_Fig03_SE_v2022.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 3: Gradient Map texture and Instance Range

+---------------------------------------------------------------------------------------+-----------------------+---------------------------------------------------------------------------------------+
| ::: {}                                                                                |                       | ::: {}                                                                                |
| +-----------------------------------+-----------------------------------------------+ |                       | +-----------------------------------+-----------------------------------------------+ |
| | ![](images/NewItem_663.png)       | Gradient Map Example                          | |                       | | ![](images/NewItem_664.png)       | Gradient Map Example                          | |
| |                                   |                                               | |                       | |                                   |                                               | |
| |                                   | ![](images/Instance_Range_Fig04_SE_v2022.jpg) | |                       | |                                   | ![](images/Instance_Range_Fig05_SE_v2022.jpg) | |
| +-----------------------------------+-----------------------------------------------+ |                       | +-----------------------------------+-----------------------------------------------+ |
| :::                                                                                   |                       | :::                                                                                   |
|                                                                                       |                       |                                                                                       |
| Figure 4: The Gradient Map and Instance Range NodeGraph used in Figure 3              |                       | Figure 4a: The Gradient Map and Instance Range NodeGraph used in Figure 3             |
+---------------------------------------------------------------------------------------+-----------------------+---------------------------------------------------------------------------------------+
|                                                                                       |                       |                                                                                       |
+---------------------------------------------------------------------------------------+-----------------------+---------------------------------------------------------------------------------------+
