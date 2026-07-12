The UVW Transform texture takes an input texture and applies a map to transform the input texture's UV layout on top of the its own UV coordinate transformation (figure 1).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_249.png)       | UVW Transform                                |
|                                   |                                              |
|                                   | ![](images/UVW_Transform_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: The UVW Transform node used to modify texture placement 

The UVW Transform texture can work with other mapping textures like the Triplanar Map texture, Mix texture (figure 2), Cosine Mix texture, logical texture maps like Comparison, or arithmetic texture maps like Add, Subtract, and Multiply.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_250.png)       | Mix Texture                                  |
|                                   |                                              |
|                                   | ![](images/UVW_Transform_Fig02_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 2: UVW Transform texture connected to a Mix texture

Below are some examples of combining different scales/orientations/translations of the same texture to create a larger detail without creating obvious patterns.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_251.png)       | Combining Textures                           |
|                                   |                                              |
|                                   | ![](images/UVW_Transform_Fig03_SE_v2023.png) |
+-----------------------------------+----------------------------------------------+

Figure 3: Combining different scales, orientations, and translations using UVW Transform
