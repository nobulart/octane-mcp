The LiveDB is OctaneRender's asset database that stores m[aterials](javascript:void(0);), node groups, and even whole scenes shared by the OctaneRender® community and team. The asset database makes it easier to move these assets across a myriad of OctaneRender plugins as well as Standalone scenes.

Most materials contain textures with images. The associated images are downloaded and saved to disk in a cache folder, and the material name is added to the path. You can see the folder\'s location by selecting an image associated with a LiveDB file and looking at the top of the Node Inspector (Figure 1).

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_130.png)       | Live DB Cache                          |
|                                   |                                        |
|                                   | ![](images/Live_DB_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------+

Figure 1: Images downloaded with LiveDB assets are stored in a cache folder

To download one of the Live DB assets, open the LiveDB tab in the Scene Outliner, right-click on the Node you want to use, then click Copy. Next, right-click in the Nodegraph Editor and click on Paste from the context menu to paste the Node into your scene. You can examine the Node\'s contents by double-clicking on the Nodegraph icon (Figure 2).

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_131.png)       | Importing Live DB Assets             |
|                                   |                                      |
|                                   | ![](images/LiveDB_Fig02_SE_2026.jpg) |
+-----------------------------------+--------------------------------------+

Figure 2: Pasting Nodes from the LiveDB into your OctaneRender scene

+-----------------------------------------------------------------------+
| NOTE                                                                  |
|                                                                       |
| The option to upload to the LiveDB is no longer availabe.             |
+-----------------------------------------------------------------------+
