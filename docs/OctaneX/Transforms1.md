Transforms provide control over the texture map placement on object surfaces. Most Projection and Generator nodes offer similar controls, but the Transform nodes provide an additional level of control for texture placement. The values in a Transform node are multiplied by the identical values in a Projection or Generator node. You can also use the Transform nodes to control geometry object placement in a scene. The Transform nodes can be accesses by right-clicking in the Nodegraph Editor and going to the Transforms menu item (Figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_308.png)       | Transform Nodes                           |
|                                   |                                           |
|                                   | ![](images/Transforms_Fig01_SE_v2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: Accessing the Transforms list in the Nodegraph Editor

 

Transforms are often paired with a projection node in order to place a texture map on an object\'s surface (Figure 2).

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_309.png)       | Transform with Projection Node           |
|                                   |                                          |
|                                   | ![](images/Transforms_Fig02_SE_2026.jpg) |
+-----------------------------------+------------------------------------------+

Figure 2: A 2D Transform node paired with a Box projection to orient a Checks texture
