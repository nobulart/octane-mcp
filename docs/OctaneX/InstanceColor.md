The Instance Color texture holds an image, and prepares each image pixel to map to geometric instance IDs. Just as a [Lua](javascript:void(0);) script or any of the OctaneRender® plugins can generate object instances, these same processes can assign IDs to each of the instances generated, which results in a grid of instance IDs. You can then assign colors to each instance ID via a Texture node (in this case with an image in the Instance Color texture), and match the IDs with pixels of the image, starting at the bottom-left and moving up to the top-right.

For the example below, there are 10x10 instances, and since a Lua script assigns IDs to each instance, OctaneRender generates 100 IDs.

+-----------------------------------+-------------------------------------+
| ![](images/NewItem_217.png)       | 10x10 Grid of Instanced Cubes       |
|                                   |                                     |
|                                   | ![](images/instance_color_Fig1.png) |
+-----------------------------------+-------------------------------------+

Figure 1: A cube and 99 instances of the same cube are shown here, forming a 10x10 grid of cubes

 

You can plug an image with 10x10 pixels into the Instance Color texture to match these dimensions. OctaneRender maps each pixel and assigns them to the instance IDs.

+-----------------------------------+-------------------------------------+
| ![](images/NewItem_218.png)       | Color Texture                       |
|                                   |                                     |
|                                   | ![](images/instance_color_Fig2.png) |
+-----------------------------------+-------------------------------------+

Figure 2: 10x10 grid with four colors

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_219.png)       | Nodegraph Layout                            |
|                                   |                                             |
|                                   | ![](images/instance_color_Fig3_389x283.png) |
+-----------------------------------+---------------------------------------------+

Figure 3: The Nodegraph layout for Figure 2

 

You can also use an existing image\'s dimensions as the basis for creating the instances. You can create the instances and assign an ID to each instance by a Lua script, or by an OctaneRender plugin, or any other standard object scatter plugins supported by OctaneRender®.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_220.png)       | Instanced Color                              |
|                                   |                                              |
|                                   | ![](images/instance_color_Fig5_1439x569.png) |
+-----------------------------------+----------------------------------------------+

Figure 4: Instance Color example with defined IDs

 

Since OctaneRender stores the colors as a texture, this option is more flexible compared to storing the colors with the geometry, since you can specify more than one color per instance.
