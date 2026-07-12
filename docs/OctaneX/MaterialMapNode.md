The [Material](javascript:void(0);) Map node takes one Geometry input and creates unfilled input pins equal to the number of materials applied to the original geometry (figure 1). The node can be found under the Geometry category in the Nodegraph Editor window. It retains the names of the materials used on the original geometry it is connected to, and allows for the connection of new materials on each of its Material input pins. Using a Material Map node lets you retain all the original elements of the mesh or geometry by making the material mapping changes on the Material Map node.

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_46.png)        | material map node                                |
|                                   |                                                  |
|                                   | ![](images/Material_Map_Node_Fig01_SE_v2021.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: A Material Map node is used to extract material input pins from an imported [Alembic](javascript:void(0);) file
