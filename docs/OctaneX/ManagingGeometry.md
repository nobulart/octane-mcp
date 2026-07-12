This section covers the primary nodes available to create and manage geometry in Octane Standalone. Once you import a scene into OctaneRender®, connect it to the Render Target. To combine multiple objects, use the Group node. If you need to reposition an object, connect a Placement node between the object and the Render Target The settings within the Placement node can set the position, and a Mesh node can connect to multiple Placement nodes, each with its own settings, to create many instances of the same object.

To determine how Octane renders meshes and scenes, you can adjust the settings in the Geometry Import tab of Preferences. You can also access the mesh settings by clicking on the Wrench icon in the Node Inspector when you select the Mesh node (figure 1). Settings for units, smoothing, and subdivision are found in the Import options.

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_598.png)       | Import Preferences                               |
|                                   |                                                  |
|                                   | ![](images/Managing_Geometry_Fig01_SE_v2026.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: Accessing the Import Preferences from the Node inspector

### Support For FBX, Alembic, And glTF

OctaneRender supports loading FBX, Alembic, and glTF files. These file formats load as a geometry archive, i.e. a Node Graph with lots of stuff inside and providing material and object layer input linkers as well as camera and geometry output linkers.

Although OctaneRender supports bones, it does not support inverse kinematic (IK) animations. This means it is necessary to convert any IK animation to forward kinematic (FK) to make the FBX files work in OctaneRender.

### Support For Bone Deformations

To support FBX and glTF, OctaneRender has support for bone deformations. Character animations can be more lightweight than if the deformed geometry needs to be baked, as in the case with Alembic. 

+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| IMPORTANT                                                                                                                                                                                                                                                                                              |
|                                                                                                                                                                                                                                                                                                        |
| Bone deformations are set up in the respective source 3D modeling applications, and are not editable from the Nodegraph Editor. At this stage, the Bone Deformation node and the Joint node exists for the benefit of the FBX and gITF files, and potential optimizations in the geometry compilation. |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

### Support For USD/Hydra

There is now native support for USD scene import and USD as the default format in Octane and [ORBX](javascript:void(0);) for scene interchange-ability between DCC plugins and standalone. Multi-render allows Octane to swap to any other rendering engine (including standard Hydra Render Delegates) in seconds. This brings completely new renderers into Octane core, including OTOY Brigade (real time path tracing engine), OTOY AnimeRender, Autodesk Arnold and Cycles.
