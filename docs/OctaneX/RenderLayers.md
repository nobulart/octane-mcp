Render Layers are used to isolate objects as a separate primary render using a specified Render Layer ID found in the Object Layer node for each scene object (figure 1). 

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_578.png)       | Object Layer Node                           |
|                                   |                                             |
|                                   | ![](images/Render_Layers_Fig01_SE_2024.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 1: Specifying the Render Layer ID on a scene object

The effects of the render layer are determined by the Active Layer ID parameter located in a Render Target node under the Render Layer rollout.. Render Layers are activated by the Enable toggle, and, when enabled, the output of the primary render (Beauty) will be determined by the Active Layer ID, all other scene components will be omitted from the primary render (figure 2). The output result is also affected by the Alpha Channel output setting found in the Kernel settings. 

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_579.png)       | Render Layer Node                           |
|                                   |                                             |
|                                   | ![](images/Render_Layers_Fig02_SE_2024.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 2: Enabling a specified Render Layer in the Render Target node and activating the Alpha Channel
