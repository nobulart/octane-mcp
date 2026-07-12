OctaneRender® supports infinite planes through the Plane primitive. Infinite planes are useful for working on scale models, allowing the camera to zoom out infinitely (figure 1). It is applicable in space-expansive scenes like outer space, oceans, and cityscapes, and makes it possible to see the entire scope of a scene as it sits on a vast and never-ending terrain. The node can be found under the Geometry category in the Nodegraph Editor window.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_50.png)        | plane node scene                  |
|                                   |                                   |
|                                   | ![](images/terrain_891x416.png)   |
+-----------------------------------+-----------------------------------+

Figure 1: Image of terrain and plane in scene

 

The Plane primitive is represented by the Plane geometry node, and can take a Material input (figure 2). You can add up to four infinite planes to a scene using the Plane geometry node. The UV mapping is aligned with the X/-Z coordinate axis, but you can also apply a transformation to the object using the Placement and Scatter nodes. [Displacement](javascript:void(0);) mapping does not work on infinite planes.

+-----------------------------------+-------------------------------------+
| ![](images/NewItem_502.png)       | plane node graph editor             |
|                                   |                                     |
|                                   | ![](images/Plane_Fig01_SE_2026.jpg) |
+-----------------------------------+-------------------------------------+

Figure 2: Image of Plane node in the Nodegraph
