Before importing geometry, you need to customize import default settings. This can be done by clicking on Preferences, then clicking on the Geometry Import tab (Figure 1).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_33.png)        | import settings                                    |
|                                   |                                                    |
|                                   | ![](images/Importing_Exporting_Fig01_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: The Geometry Import settings in the Octane preferences

### Importing gEOMETRY INTO The Scene

To import assets into OctaneRender®, move the mouse to the Graph Editor and right-click inside it to bring up the context menu with the node options list. Click on the Geometry, category to access the geometry import nodes (figure 2).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_34.png)        | import options                                     |
|                                   |                                                    |
|                                   | ![](images/Importing_Exporting_Fig02_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 2: Use the context menu on the Octane Graph editor to import assets

### Asset Import/Export Nodes

Decal - Creates a Decal node used with the [decal texturing system](DecalGeometry.md).

Gaussian Splat - Imports a .ply file for rendering gaussian splat-based point clouds. 

Mesh - Imports OBJ files. 

Mesh Volume & Mesh Volume SDF - Imports an OBJ file to be converted to a volume or SDF. 

Reference - Imports an OCS or ORBX file as a reference, without necessarily loading them.

Scene - Imports an [Alembic](javascript:void(0);), [FBX](javascript:void(0);), or USD file.

Vectron - Loads OSL files.

Volume & Volume SDF -  Imports VDB files to be rendered as volumes or SDFs. 

Geometry Exporter - Exports scene elements out of Octane in either [FBX](javascript:void(0);) or [Alembic](javascript:void(0);) format

#### Reloading Textures, Images, And Objects

While working on a scene, you may need to reload or replace some textures or objects. At the top of any Object or Image node is the active path to that image or object. Click on the Load icon to the left of the path to choose a different file while keeping the rest of the scene intact. Click on the Reload icon to reload the object or image (Figure 3).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_597.png)       | Load & Reload                                      |
|                                   |                                                    |
|                                   | ![](images/Importing_Exporting_Fig03_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 2: Load and Reload icons

#### Exporting Scenes

In addition to saving scenes in .osc and .orbx formats, there is a new node available in the Nodegraph Editor window under the Utility category titled Geometry Exporter (figure 3). This node can be used to export the scene in either .fbx or .abc (Alembic) format.

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_36.png)        | exporting scene                                    |
|                                   |                                                    |
|                                   | ![](images/Importing_Exporting_Fig04_SE_v2022.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 4: Exporting the scene in either FBX or Alembic format using the Geometry Exporter node
