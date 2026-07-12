The Round Edges node rounds off geometry edges by using a shading effect instead of creating additional geometry. It's best used for rounded edges that will appear small in the final render.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_134.png)       | Round Edges Node                           |
|                                   |                                            |
|                                   | ![](images/Round_Edges_Fig01_SE_v2020.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 1: Round Edges parameters

 

### Round Edges Parameters

Mode - The Fast mode uses the rounding method introduced in OctaneRender® v3. The Accurate mode produces better-looking results, but may be slower. Accurate mode can select the affected edges by using the Concave Only or Convex Only options.

Radius - The rounded edge\'s radius.

Roundness - Controls the rounded edge\'s shape. A value of 1 is completely round, while 0 is a chamfer.

Samples - The number of rays to use when sampling neighboring geometry.

Consider Other Objects - Controls how rounded edges are applied to different objects. When enabled, intersections between different objects are rounded. When disabled, only the current object is considered.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_135.png)       | Consider Other Objects                          |
|                                   |                                                 |
|                                   | ![](images/RoundEdges_ConsiderOtherObjects.png) |
+-----------------------------------+-------------------------------------------------+

Figure 2: Consider Other Objects (left is disabled, right is enabled)
