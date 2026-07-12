[ORBX](javascript:void(0);)® packages can be created and unpacked from the File menu (Figure 1). 

+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| USEFUL INFO                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| [The ORBX file format is the best way to transfer scene files from 3D Authoring software programs that use the Octane Plug-in such as Octane for Maya, Octane for Cinema 4D, or OctaneRender Standalone. This format is more efficient than FBX when working with Octane specific data as it provides a flexible, application independent format. ORBX is a container format that includes all animation data, models, textures etc. that is needed to transfer an Octane scene from one application to another.](javascript:void(0);) |
+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_30.png)        | saving orbx package                               |
|                                   |                                                   |
|                                   | ![](images/Packager_ORBX_File_Fig01_SE_v2020.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: Saving the Node Graph as an ORBX package

The packager stores selected Node Graphs into an ORBX archive. The node graph can be an entire scene, an individual material or texture node setup, or a group of selected nodes. The ORBX archive is not compressed, so the files can get large.

### Creating A Node Graph And Storing It As A Package

To create a Node Graph:

1.  1.  Right-click on the Node Graph Editor and click on Node Graph.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_31.png)        | creating a node graph                                 |
|                                   |                                                       |
|                                   | ![](images/Packager_And_ORBX_File_Fig01_SE_v2021.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 2: The Node Graph option

1.  1.  Build the scene inside the Node Graph Editor by double-clicking the Node Graph node to open up the new tab labeled Node Graph. Build the scene on the Node Graph within this tab. Figure 3 shows the Node Graph of the screws scene shown in Figure 1. You can rename the Node Graph by selecting it and double-clicking on its label in the Node Inspector, then entering a descriptive name. The Node Graph you want to package can contain any type of OctaneRender® node or Node Graph.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_32.png)        | node graph layout                 |
|                                   |                                   |
|                                   | ![](images/Packager3_743x351.jpg) |
+-----------------------------------+-----------------------------------+

Figure 3: The node graph for the screws scene is built within the Node Graph tab

1.  1.  When you want to export the Node Graph, click on the File menu, then click Save As Package. Use the dialog box to select where you want to store the ORBX file on your local drive.
    2.  You can save all types of nodes and node groups to the hard disk as packages, including the connections between them. The packaged Node Graph can be an entire scene made up of connected Nodes, or a lighting setup that you\'d like to use in other OctaneRender scenes, or your favorite OctaneRender materials. You can also combine Nodes and create a Node Graph node by selecting the Nodes to group in the Nodegraph Editor, then right-click on one of the selected nodes and click on Group Items.
