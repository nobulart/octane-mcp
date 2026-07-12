The Placement node can be used to add an additional layer of position, rotation, and scale data to an object (figure 1). The node can be found under the Geometry category in the Nodegraph Editor window. This data will be added to any translate, rotate, and scale data set in the Geometric Primitive node. This node consists of two input pins, one for the geometry and one for a transformation node. If a transformation node is connected, it\'s parameters will override the Placement node\'s default parameters.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_49.png)        | placement node                             |
|                                   |                                            |
|                                   | ![](images/Placement_Fig01_SE_v2020_2.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 1: The Placement Node and its associated parameters

The Placement node has parameters for Rotation, Scale, and Translation on all three axes. There is also a parameter for selecting different axes combinations for the Rotation Order.
