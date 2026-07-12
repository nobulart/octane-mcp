The Normal texture node is used to sample normals for the surface of an object. This data can then be used to mix other texture maps or materials together (figure 1).

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_226.png)       | Normal                                |
|                                   |                                       |
|                                   | ![](images/Normal_Fig01_SE_v2021.jpg) |
+-----------------------------------+---------------------------------------+

Figure 1: The Normal node used to blend together two Floats to Color nodes in a Mix Texture node

 

### Normal Parameters

Normal Type - Determines the type of normal to sample.

Coordinate System - Determines the coordinate space used to calculate the normal.

Normalize Result - Determines whether to remap the normal data to the 0 to 1 range or leave it in the -1 to 1 range.
