Perspective mapping takes the world space coordinates and divides the X and Y coordinates by the Z coordinate (Figure 1). One way this is useful is by using a texture with this projection as the distribution, with black border mode. You can also use it for camera mapping. The same change as the other projections applies here: the image is mapped to (-1, -1) -- (1, 1), so by default, offsets are not needed to use this mapping for projectors or camera mapping. The Use Rest Attribute option keeps texture maps from distorting when the geometry is animated. 

+-----------------------------------+---------------------------------------------------------+
| ![](images/NewItem_299.png)       | Perspective                                             |
|                                   |                                                         |
|                                   | ![](images/Perspective_Projection_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+---------------------------------------------------------+

Figure 1: The Perspective projection node orienting a Checks texture

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_300.png)       | Various Perspective Projections                |
|                                   |                                                |
|                                   | ![](images/projectionsperspective_735x367.png) |
+-----------------------------------+------------------------------------------------+

Figure 2: Perspective projection applied to a box, cylinder, and sphere
