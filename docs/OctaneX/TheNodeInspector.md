A scene in OctaneRender® consists of a group of Nodes, and each Node has attributes. In turn, each attribute holds a value parameter depending on the type of data the attribute requires. These values can be numerical, boolean, modal, or even another node. You manipulate these attributes with the Node Inspector.

The Node Inspector (Figure 1) can change nearly every aspect of the render/scene in OctaneRender.  Nodes that are selected in the Graph Editor are displayed in the Node Inspector where their values can be adjusted or changed.  When using the Material Picker, the currently selected material will also be displayed in the Node Inspector. To reduce the clutter, this pane also provides a compact view of uncollapsed node pins.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_8.png)         | node inspector                                |
|                                   |                                               |
|                                   | ![](images/Node_Inspector_Fig01_SE_v2022.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: A Render Target node\'s input pin correspond to the attribute list in the Node Inspector.

The Node Inspector also includes quick buttons (Figure 2) that allow the user to quickly jump to the most commonly used nodes (RenderTarget, Camera, Resolution, Environment, Imager, Kernel, and Current Mesh). It also has context menus allowing to copy, paste, and fill empty node pins.

![](images/Node_Inspectors_Fig02_SE_v2022.jpg)

Figure 2: Quick access buttons in the Node Inspector.

The bottom of the Node Inspector window hosts the OctaneLive and Online status. (Figure 3).

![](images/Node_Inspector_Fig03_SE_v2020.jpg)

Figure 3: The Octane Status line.

### Renaming Nodes

You can rename individual Nodes and node groups through their respective Node equivalents in the Node Inspector pane (Figure 4).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_531.png)       | Node Inspector                                 |
|                                   |                                                |
|                                   | ![](images/Node_Inspectors_Fig04_SE_v2026.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 4: Node Inspector panel

### Quick Material Previews

It is possible to enable quick previews of Materials and Textures inside the Node Inspector (Figure 5). These are rendered without interrupting the main render, and OctaneRender® updates them when the Material or Texture changes. You can update the Material\'s scale too.

You can choose to preview a material on a sphere or a flat 2D image. The scale of the object shown is customizable, and you can choose default settings in the settings dialog.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_532.png)       | Previewing Material                            |
|                                   |                                                |
|                                   | ![](images/Node_Inspectors_Fig05_SE_v2026.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 5: Preview button

To avoid disrupting the current render, turn off the Material Render icon in the Nodegraph Editor (Figure 6).

![](images/Node_Inspector_Fig06_SE_v2026.jpg)

Figure 6: Material Render icon
