[Render Passes](javascript:void(0);) or AOVs  are artist-specified render and data passes generated at render time that can be used for compositing, checking shader output, debugging issues, etc. AOVs can output a variety of different image output passes, as well as include data passes such as normals, object positions, material IDs, motion vectors, etc. AOV nodes can create simple composites inside of Octane, which can be seen in the Render Viewport window, as well as output as freestanding files to be used in external compositing applications.The Render AOVs can then be composited directly in Octane using the Output AOV nodes.

In addition to access from the Node Graph Editor window, the Render AOVs are accessible from the Node Inspector window without adding and connecting a specific Render AOV node to the scene - click on the Render AOV icon in the Node Inspector and choose the desired AOV from the drop down list (figure 1).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_474.png)       | Render AOVs                                  |
|                                   |                                              |
|                                   | ![](images/Render_Passes_Fig01_SE_v2024.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: Accessing AOVs using the icon next to the Node Inspector

Multiple AOVs can be added using the above method by first selecting Render AOV Group from the AOV list (figure 2). More AOV slots can be added by clicking on the Add Render AOV button.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_475.png)       | Render AOV Group                             |
|                                   |                                              |
|                                   | ![](images/Render_Passes_Fig02_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 2: Adding the Render AOV Group node to apply multiple AOVs

 

### Render AOV Group Node Parameters

Raw - Converts the Beauty AOVs to raw AOVs by factoring out the color of the BxDF of the surface hit by the camera ray.

Cryptomatte Bins - Determines the number of cryptomatte bins to render.

Cryptomatte Seed Factor - Determines the amount of samples to use for seeding cryptomattes.

Max Info Samples - The maximum number of samples for the info passes.

Info Sampling Mode - Enables motion blur and [depth of field](javascript:void(0);) along with setting pixel filtering modes.

- Distributed Rays - Enables motion blur and [DOF](javascript:void(0);) as well as enabling pixel filtering.
- Non-Distributed with Pixel Filtering - Disables motion blur and DOF, but leaves pixel filtering enabled.
- Non-Distributed without Pixel Filtering - Disables motion blur and DOF, and disables pixel filtering for all AOVs except for Render Layer Mask and Ambient Occlusion.

Info Opacity Threshold - Geometry with an opacity equal to or higher than this value is treated as completely opaque.

 

AOVs can be added as individual nodes in the NodeGraph Editor window as well. You can add an AOV node by right-clicking in the Nodegraph Editor and clicking on Render AOVs (figure 3).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_476.png)       | Render AOvs Node Graph Editor             |
|                                   |                                           |
|                                   | ![](images/Render_AOVs_Fig03_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 3: Add AOV nodes in the Node Graph Editor window

Multiple AOVs nodes can be added and connected via a Render AOV Group (figure 4).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_477.png)       | Render AOV Group Node                     |
|                                   |                                           |
|                                   | ![](images/Render_AOVs_Fig04_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 4: A [Diffuse](javascript:void(0);) AOV and Cryptomatte AOV connected via a Render AOV Group node

The Render AOVs can be viewed by selecting their correspinding buttons in the Render Viewport window (figure 5)

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_482.png)       | Viewing AOVs                              |
|                                   |                                           |
|                                   | ![](images/Render_AOVs_Fig05_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 5: Viewing the Render AOVs in the Render Viewport window
