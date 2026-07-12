The Random Color texture generates a random float value that creates color variations on geometry instances connected to a single material. Figure 1 shows a number of instances of the OctaneRender® logo geometry. A single [Diffuse](javascript:void(0);) material applies to all of the instances. Each instance has a random shade because the Random Color texture node connects to the material\'s Diffuse channel.

Figure 2 shows a graph of the network. OctaneRender® creates these instances by connecting the Geometry node to multiple Placement nodes. The Random Color texture is useful when importing baked particle simulations that contain thousands of instances. OctaneRender® can apply a aterial to the instances, and the Random Color texture can connect to different [Material](javascript:void(0);) channels to create variations in the instance shading. The Random Color texture has a single parameter - Random Seed. Changing this value shifts the random output of the texture.

+-----------------------------------+-------------------------------------+
| ![](images/NewItem_232.png)       | Random COlor Texture                |
|                                   |                                     |
|                                   | ![](images/randomColor_939x454.png) |
+-----------------------------------+-------------------------------------+

Figure 1: Several instances of the same geometry have random shading after connecting a Random Color texture to the instance\'s Material

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_498.png)       | nodegraph layout                       |
|                                   |                                        |
|                                   | ![](images/randomColor01_1137x709.png) |
+-----------------------------------+----------------------------------------+

Figure 2: A Nodegraph of the geometry instances network
