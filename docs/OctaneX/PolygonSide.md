The Polygon Side node assigns black or white values based on a Polygon object\'s normal direction. This is useful for assigning different Textures or Materials to different sides of a Polygon object.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_228.png)       | Nodegraph Layout                  |
|                                   |                                   |
|                                   | ![](images/polygonSide01.png)     |
+-----------------------------------+-----------------------------------+

Figure 1: A Polygon Side node controls the Mix texture node and the blending amount of green and red RGB Color nodes

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_229.png)       | Polygon Side Parameters               |
|                                   |                                       |
|                                   | ![](images/polygonSide02_898x248.png) |
+-----------------------------------+---------------------------------------+

Figure 2: [Diffuse material](javascript:void(0);) parameters

 

The result connects to the OctaneRender® material\'s [Diffuse](javascript:void(0);) channel, which applies to a twisted polygon.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_230.png)       | Polygon Side Example              |
|                                   |                                   |
|                                   | ![](images/polygonSide2.png)      |
+-----------------------------------+-----------------------------------+

Figure 3: A twisted surface with a red texture mapped to one side of the polygon and a green texture mapped to the other
