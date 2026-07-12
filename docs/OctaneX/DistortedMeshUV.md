The Distorted Mesh UV node will distort the UVs of a mesh object using the inputs connected to the Rotation, Scale, and/or Translation input pins (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_294.png)       | Distorted Mesh UV                                |
|                                   |                                                  |
|                                   | ![](images/Distorted_Mesh_UV_Fig01_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: An imported texture map\'s UVs are distorted using the Distorted Mesh UV node

 

### Distorted Mesh UV Parameters

Rotation - Amount of rotation applied to the UVs, normalized to the rotation range. A value of 0 (black) rotates the UVs by the minimum value in the Range and a value of 1 (white) rotates the UVs by the maximum value in the Range.

Rotation Range - Range of rotation in degrees.

Scale - Amount of scale applied to the UVs, normalized to the scale range. A value of 0 (black) scales the UVs by the minimum value in the Range and a value of 1 (white) scales the UVs by the maximum value in the Range.

Scale Range - Range of scaling.

Translation - Amount of translation applied to the UVs, normalized to the translation range. A value of 0 (black) translates the UVs by the minimum value in the Range and a value of 1 (white) translates the UVs by the maximum value in the Range.

Translation Range - Range of translation.
