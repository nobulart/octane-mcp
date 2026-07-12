The Triplanar projection works in conjunction with a Triplanar map. It takes the coordinates in world or object space and will pick the projection axis depending on the active axis of the Triplanar map node. This gives a quick way to map a texture on any object, and presents the possibility for texture transforms local to each projection axis. The Triplanar map node has six input pins representing the positive and negative X, Y, and Z planes. You can map the same or different texture nodes to each of these input pins.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_304.png)       | Triplanar Projection                                  |
|                                   |                                                       |
|                                   | ![](images/Triplanar_Projection_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: The Triplanar map and the Triplanar projection map a Checks texture and a Marble texture to an object\'s different projection planes

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_305.png)       | Various Triplanar Projections                |
|                                   |                                              |
|                                   | ![](images/projectionstriplanar_740x342.png) |
+-----------------------------------+----------------------------------------------+

Figure 2: Triplanar projection applied to a box, cylinder, and sphere
