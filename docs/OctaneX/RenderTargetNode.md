The Render Target is the node that is referenced as an output point for the rendered scene. It offers powerful flexibility when setting up advanced scenes, as it hooks up to everything that forms part of the scene including the geometry, materials, environment, camera, and the render kernel. Multiple Render Targets allows for various scene configurations within the same file.

To create a Render Target node, right-click in the Nodegraph Editor and click on Render Target (figure 1).

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_438.png)       | Render Target                                     |
|                                   |                                                   |
|                                   | ![](images/Render_Target_Node_Fig01_SE_v2021.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: Adding a Render Target node

 

The Render Target node provides the set of default parameters listed below. Each parameter has an associated pin for connecting appropriate nodes.

- Camera
- Environment
- Visible Environment
- Geometry
- Film Settings
- Animation
- Kernel
- Render Layer
- Render AOVs
- Output AOVs
- Imager
- [Post Processing](javascript:void(0);)

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_439.png)       | Input Connections                                 |
|                                   |                                                   |
|                                   | ![](images/Render_Target_Node_Fig02_SE_v2026.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 2: The Render Target node input connections

The Mesh node pin accepts geometry such as a polygon mesh (OBJ), or an [Alembic](javascript:void(0);) scene (ABC). It also accepts geometry groups and instances.

You can set the image resolution for each preview Render Target through its Resolution node in the Node Inspector.

Each Render Target also has a default Kernel and this will be visible in the Node Inspector while that particular Render Target is selected. For more information regarding [Kernels](javascript:void(0);), see the specific Kernel topics in the Rendering Overview category of this manual.

Appropriate node connections are shown below (figure 3). Using specific nodes instead of adjusting the default Render Target parameters offers greater flexibility and customization.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_440.png)       | Connecting Nodes                                  |
|                                   |                                                   |
|                                   | ![](images/Render_Target_Node_Fig03_SE_v2026.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 3: Connecting nodes to the Render Target to customize the render output

The following examples illustrate how multiple Render Targets can connect to the same scene. In the Figure 4, the Render Target node is active and it has different settings for F-Stop, and camera placement than the second example shown in Figure 5, where the Render Target (2) node is active.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_441.png)       | Multiple Render Targets           |
|                                   |                                   |
|                                   | ![](images/RenderTaget2.jpg)      |
+-----------------------------------+-----------------------------------+

Figure 4: The Render Viewportshows the result generated when you select the first Render Target

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_442.png)       | Multiple Render Targets           |
|                                   |                                   |
|                                   | ![](images/RenderTaget3.jpg)      |
+-----------------------------------+-----------------------------------+

Figure 5: The Render Viewport shows the result generated when you select the second Render Target
