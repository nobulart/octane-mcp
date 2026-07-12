The Geometry Exporter node is used to export scene elements out of Octane in either [FBX](javascript:void(0);) or [Alembic](javascript:void(0);) format. The node can be found under the Geometry category in the Nodegraph Editor window (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_42.png)        | geometry exporter                                |
|                                   |                                                  |
|                                   | ![](images/Geometry_Exporter_Fig01_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: Accessing the Geometry Exporter node

The Geometry Exporter node provides numerous parameters for exporting a scene in FBX or Almebic format (figure 2).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_43.png)        | geometry exporter parameters                     |
|                                   |                                                  |
|                                   | ![](images/Geometry_Exporter_Fig02_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 2: The Geometry Exporter node\'s parameters

### Geometry Exporter Parameters

Play Button - Executes the exporting of the FBX or Alembic file. 

Output File - Chooses the output path for either the FBX or Alembic file.

Export [Materials](javascript:void(0);) - When exporting in FBX format, this option will also export additional nodes attached to material nodes.

Texture Quality - When exporting in FBX format and Export Materials is selected, this option determines the resolution of exported texture maps.

Perserve Octane [Material](javascript:void(0);) Data - When exporting in FBX format, this option will export Octane material types in their original format instead of converting all exported material types to Universal materials.
