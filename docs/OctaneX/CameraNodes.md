In OctaneRender®, a default camera is always present in a scene. Additionally, there are several different types of camera nodes that can be added to the Nodegraph Editor. The primary Camera node type is the Thin Lens Camera. Camera nodes are connected to the Camera input pin on a Render Target node (figure 1). There can be multiple camera nodes present in the Nodegraph Editor, allowing multiple camera locations to render a scene.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_371.png)       | Thin Lens Camera                            |
|                                   |                                             |
|                                   | ![](images/Camera_Nodes_Fig01_SE_v2026.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 1: A Thin Lens Camera node is connected to the Camera input pin on a Render Target node

Camera node attributes are accessible without adding a Camera node to the scene by clicking on the Current Camera icon in the Node Inspector (figure 2).

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_372.png)       | Node Inspector                    |
|                                   |                                   |
|                                   | ![](images/Cameras2.jpg)          |
+-----------------------------------+-----------------------------------+

Figure 2: Access camera settings by clicking on the Camera icon in the Node Inspector

 

Camera nodes are also accessible by right-clicking in the Nodegraph Editor and choosing Cameras (figure3). These nodes can then be connected to the Camera pin of a Render Target node.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_373.png)       | Node Graph Editor                           |
|                                   |                                             |
|                                   | ![](images/Camera_Nodes_Fig03_SE_v2023.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 3: Use the pop-up menu to add Camera nodes

There are seven types of camera nodes available for adjusting the camera settings: Thin Lens Camera, Panoramic Camera, Baking Camera,Realistic Lens Camera, two kinds of OSL Cameras and the Universal Camera.Additionally, there is a Camera Swtich node which allows for more than one camera to be connected to the Camera pin on a Render Target node.
