The Node Graph Editor lets you view the nodes associated with the current scene (Figure 1). The Render Target encompasses all of the scene-related nodes: Camera, Environment, Visible Environment, Geometry, Film Settings (which specifies the resolution), animation settings, Kernel, Render Passes, Render Layer, AOV Output Group, Imager, and post-processing nodes. Selecting a Node in the Graph Editor brings up that Node\'s settings up in the Node Inspector along with its empty Node pins. You can fill empty node pins in the Graph Editor or the Node Inspector. Placing the mouse cursor over a Node pin shows the name of the Material contained by that pin.

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_522.png)       | Node Graph Editor                      |
|                                   |                                        |
|                                   | ![](images/TheGraphEditor_656x341.png) |
+-----------------------------------+----------------------------------------+

Figure 1: Node Graph Editor

You can move around the Node Graph Editor with the mouse by clicking and dragging the yellow area on the thumbnail preview at the top-left corner of the Graph Editor (Figure 2). You can also zoom in and out of the Nodegraph Editor by using your mouse\'s scroll wheel or pan using the right mouse button.

![](images/TheGraphEditor1.png)

Figure 2: The Node Graph\'s viewable area

### Adding Nodes In The Node graph Editor

To add more nodes, right-click on an empty area to bring up the context menu with the Node options.  After selecting, the new node is placed on the cursor location (Figure 3).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_523.png)       | Accessing Nodes                             |
|                                   |                                             |
|                                   | ![](images/Graph_Editor_Fig03_SE_v2022.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 3: Adding nodes to the Nodegraph Editor window

### Node Context Menus

Right-clicking on a node brings up a context menu with options to delete all selected nodes, save the selected nodes as a macro file or in LocalDB, and render the node under the cursor (Figure 4). The Group Items option creates a single group node that represents the selected nodes. Grouping nodes is useful if you want to hide complex Node systems. Node pin connections are saved when you save multiple nodes. The context menu also includes Show In Outliner, which will quickly pick and select the respective node's corresponding element in the Outliner.

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_524.png)       | Node Context Menu                    |
|                                   |                                      |
|                                   | ![](images/TheGraphEditor3_SEv4.png) |
+-----------------------------------+--------------------------------------+

Figure 4: Node context menu

### Selecting Multiple Nodes

Start dragging in an empty area of the node graph editor to select multiple nodes with a box (Figure 5). Hold down the Shift key to add additional nodes to the current selection. You can also add and remove nodes from the selection by holding down Ctrl and clicking on a node. The Node Graph Editor supports copy and paste operations by right-clicking on selected nodes to invoke a context menu of command options, or by simple keyboard shortcuts Ctrl+C for copy and Ctrl+V for paste. There are also application-wide shortcuts for cut, copy, paste, and delete commands in the application menu (Figure 6). Copying and pasting nodes also duplicates connections coming from other nodes to the copied Nodes. Dropping macro and mesh files on the Node Graph Editor is also possible.

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_525.png)       | Selecting Nodes                        |
|                                   |                                        |
|                                   | ![](images/TheGraphEditor_606x296.jpg) |
+-----------------------------------+----------------------------------------+

Figure 5: Selecting nodes

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_526.png)       | Copying Nodes                           |
|                                   |                                         |
|                                   | ![](images/TheGraphEditor4_601x285.png) |
+-----------------------------------+-----------------------------------------+

Figure 6: Copying the selected nodes

### Disconnecting Nodes

Hold down the Ctrl key, then press the left mouse button and move the cursor between nodes to disconnect them (Figure 7).

![](images/TheGraphEditor5_681x213.png)

Figure 7: Disconnecting nodes

### Hiding Complex Node Systems

For a clean and organized graph, you can group nodes together, and they are represented by a single node named Node Graph (Figure 8). You can rename the node through its node entry in Node Inspector pane. Double-clicking on a grouped node opens a new tab in the Nodegraph Editor, which shows the graph of the constituent nodes for that group. You can group together other grouped nodes to create nested groups.

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_527.png)       | Grouping Nodes                          |
|                                   |                                         |
|                                   | ![](images/TheGraphEditor6_678x384.png) |
+-----------------------------------+-----------------------------------------+

Figure 8: Group Items option

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_528.png)       | Ungrouping Nodes                        |
|                                   |                                         |
|                                   | ![](images/TheGraphEditor7_677x349.png) |
+-----------------------------------+-----------------------------------------+

Figure 9: Ungroup option

### Internal Graph And Material Previews

The Node Graph Editor has buttons to show the internal material preview scene when you select a node (Figure 10).

![](images/TheGraphEditor8_457x287.png)

Figure 10: Node Graph Editor buttons

### Node Graph Editor Navigation

You can scroll in the Node Graph Editor with the mouse wheel when holding down the CTRL key (or CMD key on Macintosh® platforms). Like the Viewport, the Node Graph Editor also has panning and zooming controls:

- Select nodes - Left mouse button
- Pan - Right mouse button
- Zoom in/out - Mouse wheel/middle mouse button

When zoomed out far enough, you can not edit connections, but you can still move items. When an item or a node is dragged out of the Node Graph Editor window, the Node Graph window auto-pans to make that node visible.

Multi-Connect - Connects multiple nodes at a time by holding down the CTRL key (or CMD key on Macintosh® platforms) while connecting some selected nodes to a pin on another node. It is inactive if only one connection is possible.

Connection Cutter - Cuts off multiple connections by holding down the CTRL key (or CMD key on Macintosh® platforms) and then click-dragging the mouse to form a line over the connections to remove.

Search Dialog - Pressing CTRL+F brings up the Search Dialog, which finds and selects nodes and dynamic pins that contain the entered search string.
