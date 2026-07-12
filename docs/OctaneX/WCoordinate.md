The W Coordinate texture can access the OctaneRender® W Coordinate System, which can place gradient colors on hair geometry. The hair geometry stores an inherent hair gradient interpolation along with hair data exported from 3D modeling applications. W is an attribute of the Mesh node, which defines a coordinate for every hair vertex per strand. This attribute is loaded from an [Alembic](javascript:void(0);) file input. However, if the attribute is not in the Alembic file, OctaneRender creates the coordinates per strand. OctaneRender uses the resulting vertex coordinates to distribute a gradient per strand, and the gradient interpolation is based on settings in the Preferences pane\'s Import tab.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_238.png)       | viewport settings                           |
|                                   |                                             |
|                                   | ![](images/W_Coordinate_Fig01_SE_v2026.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 1: Import tab settings for the Hair Gradient Interpolation

To use the W attribute for applying gradient colors to the hair data, you must plug a W Coordinate texture as the Input Texture of an OctaneRender Gradient Map (figure 2). This tells OctaneRender to render the inputs as a Gradient mapping, and OctaneRender uses the specified gradient interpolation to distribute the gradient. This is based on either the hair length or the segment count per strand, depending on what is set in the Import tab for hair geometry.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_239.png)       | Using a Gradient Map                        |
|                                   |                                             |
|                                   | ![](images/W_Coordinate_Fig02_SE_v2022.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 2: Gradient Map texture node with W Coordinates

For example, if the hair strand has three segments and each segment is a different length, the Hair Length option distributes the W evenly from root to tip. Segment Count distributes the W independent of the segment lengths, so the first segment goes from 0 to 1/3, the second segment goes from 1/3 to 2/3, and the last segment goes from 2/3 to 1 (figure 3).

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_240.png)       | Segmentation & Length                                |
|                                   |                                                      |
|                                   | ![](images/hair_data_length_vs_segments_599x591.png) |
+-----------------------------------+------------------------------------------------------+

Figure 3: Hair segmentation and length
