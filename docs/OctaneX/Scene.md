Scene nodes can be used to import [Alembic](javascript:void(0);), [FBX](javascript:void(0);), GLTF, and USD scene data. OctaneRender® can import rigid body animations from Alembic and USD files (figure 1). Loading an Alembic file loads the geometry's animated vertices, animated transforms, and the camera paths. The node can be found under the Geometry category in the Nodegraph Editor window.

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_55.png)        | scene node                           |
|                                   |                                      |
|                                   | ![](images/Scene_Fig01_SE_v2021.jpg) |
+-----------------------------------+--------------------------------------+

Figure 1: Importing an animated Alembic scene and applying a [Diffuse material](javascript:void(0);) to the inner group of the imported simulation

When you load an Alembic or USD file in the Graph Editor, the time slider becomes visible along the Render Viewport controls (figure 2).

![](images/timeSliderScreenshot_1__817x80.png)

Figure 2: Time Slider

The Alembic or USD file can contain one or more camera paths. Connect a camera path to the Render Target node\'s Camera pin to make the Octane camera move along this camera path (figure 3). You can also adjust the scene\'s scale with a Placement node in OctaneRender.

![](images/alembicScreenshot_1_.png)

Figure 3: Modifying the Camera using the Placement node

To modify materials used in the Alembic or USD scene, click on the Alembic scene node on the Graph Editor to bring up the node's parameters in the Node Inspector pane, then click on the Edit Settings icon within these parameters or connect material nodes to the input pins on the alembic scene node.
