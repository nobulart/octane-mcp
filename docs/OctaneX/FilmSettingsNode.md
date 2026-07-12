The Film Settings parameters are accessible from the Node Inspector window without adding and connecting a specific Film Settings node to the scene. Click on the Render Target node, then click the Film Settings icon in the Node Inspector to bring up the parameters (figure 1).

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_395.png)       | Film Settings                                     |
|                                   |                                                   |
|                                   | ![](images/Film_Settings_Node_Fig01_SE_v2023.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: Clicking on the Film Settings icon in the Node Inspector

You can add a Film Settings node by right-clicking in the Nodegraph Editor, then navigating to the Render Settings category and clicking on Film Settings.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_396.png)       | Node Graph Editor Access                          |
|                                   |                                                   |
|                                   | ![](images/Film_Settings_Node_Fig02_SE_v2023.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 2: Add a Film Settings node using the context menu in the Nodegraph Editor

 

### Film Settings Node Parameters

 

Resolution - Determines the scene\'s rendering resolution.

Region Start (pixel)- These are the coordinates for where the rendering region begins measured in pixels.

Region Size (pixel)- The Render Region\'s size in pixels.

Region Start - These are the coordinates for where the rendering region begins measured in percentage.

Region Size - The Render Region\'s size in percentage.

Lock Relative Region - If enabled, and the film resolution is changed, the relative film region stays constant and the absolute film region in pixels gets updated. If disabled, and the film resolution is changed, the absolute film region in pixels stays constant and the relative film region gets updated.

#### Region Rendering

##### Interactive Region Rendering

You can start Interactive region rendering at any time during the course of rendering a scene, even after reaching the maximum number of samples per pixel. Rendering continues up to 256000 region samples per pixel, or when you stop rendering. Any samples calculated for the interactive render region are counted separately in squared brackets, and are not added to the film\'s samples statistics.

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_676.png)       | Region Rendering                      |
|                                   |                                       |
|                                   | ![](images/FilmSettingsNodeFig04.png) |
+-----------------------------------+---------------------------------------+

Figure 4: Interactive region rendering

 

##### Non-Interactive Region Rendering

Sometimes you may need to re-render a subsection of a whole frame, and up to the maximum samples settings of the Kernel node. You can use the Region Start and Region Size parameters to define a region where everything else renders to black and stops at the maximum samples setting.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_677.png)       | Region Rendering                                  |
|                                   |                                                   |
|                                   | ![](images/Film_Settings_Node_Fig05_SE_v2026.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 5: Non-interactive region rendering
