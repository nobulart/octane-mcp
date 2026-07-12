The [Shadow Catcher](javascript:void(0);) material capture shadows (Figure 1). It becomes visible in areas that are in shadows, while other areas become transparent to the render (Figure 2).

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_108.png)       | Shadow Catcher Material                                |
|                                   |                                                        |
|                                   | ![](images/Shadow_Catcher_Material_Fig01_SE_v2021.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 1: Shadow Catcher parameters

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_109.png)       | Shadow Catcher with HDRI Background                    |
|                                   |                                                        |
|                                   | ![](images/Shadow_Catcher_Material_Fig02_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 2: A Model is integrated into an image using the Shadow Catching material

 

### Shadow Catcher Parameters

Enabled - The material is transparent unless there is some direct shadow cast onto the material, which makes it less transparent depending on the shadow strength.

Opacity - Controls the transparency of the shadows via a greyscale information.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

 

This feature is enabled by activating the Shadow Catcher option on the [Diffuse](javascript:void(0);) material applied to the shadow-catching surfaces (Figure 3). The Universal material also has a parameter for enabling the shadow catcher.

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_110.png)       | Diffuse Material Shadow Catcher                        |
|                                   |                                                        |
|                                   | ![](images/Shadow_Catcher_Material_Fig03_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 3: Activating the shadow catching properties in a [Diffuse material](javascript:void(0);) node.

 

There is also an independent Shadow Catcher node available in the [Materials](javascript:void(0);) category of the Nodegraph Editor (Figure 4). This node can be connected directly to Geometry nodes to be used as shadow catching objects thus bypassing the need to connect a Diffuse or Universal material.

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_111.png)       | Shadow Catcher Node                                    |
|                                   |                                                        |
|                                   | ![](images/Shadow_Catcher_Material_Fig04_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 4: Accessing the independent Shadow Catcher node in the Nodegraph Editor.

 

In the Render Kernel window, activate [Alpha Channel](javascript:void(0);) and disable Keep Environment (Figure 5). When the image renders, the shadows appear over the transparent parts of the surface. This image can work in a compositing package to merge the object and the shadows into the composition.

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_112.png)       | Alpha Channel & Keep Environment                       |
|                                   |                                                        |
|                                   | ![](images/Shadow_Catcher_Material_Fig05_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 5: Accessing the Alpha Channel and the Keep Environment options in the Render Target window.
