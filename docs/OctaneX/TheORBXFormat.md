OctaneRender® creates packages containing macro nodes otherwise known as nodegraphs. [ORBX](javascript:void(0);) packages store all the geometry, materials, animation data, textures and everything else related to the scene into a single archive file (Figure 1).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_29.png)        | orbx node graph                                 |
|                                   |                                                 |
|                                   | ![](images/ORBX_File_Format_Fig01_SE_v2020.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: A NodeGraph layout contained in an ORBX file.

This feature replaces the older method of embedding images in .ocs files. Each .orbx package can then be stored locally in the LocalDB as a shared resource for other Octane users to access. The .orbx file format can also be exported from applications such as Maya, Cinema 4D, or 3DS Max that have the Octane plugin installed and licensed. This makes it possible to move scenes and materials from host applications to Octane Standalone and the Render Network®.
