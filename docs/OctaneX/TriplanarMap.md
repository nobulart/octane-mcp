The Triplanar Map texture works in conjunction with a Triplanar projection. The Triplanar projection takes the coordinates in world or object space and it picks the projection axis, depending on the active axis of the Triplanar Map. This gives a quick way to map a texture on any object, and presents the possibility for texture transforms local to each projection axis. The Triplanar Map has six input pins representing the positive and negative x, y, and z planes. The same or different Texture nodes can map to each of these input pins (figure 1).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_243.png)       | Triplanar Map                                  |
|                                   |                                                |
|                                   | ![](images/Triplanar_Map_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: The Triplanar Map and the Triplanar projection are mapping a Check texture and an imported texture to different projection planes of an object

 

This texture maps multiple texture samples along the +-x, +-y, and +-z planes in world space or object space coordinates, and blends them to create one seamless texture. In most cases, depending on the complexity of the model, it maps textures without having a UV-mapped mesh (figure 2).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_245.png)       | +- XYZ Planes                                |
|                                   |                                              |
|                                   | ![](images/texturemaptriplanar2_697x370.png) |
+-----------------------------------+----------------------------------------------+

Figure 2: Nodes for x, y, and z planes

The Triplanar Map divides a [Material](javascript:void(0);) map into six areas corresponding to the x, -x, y, -y, z, and -z axes. A texture would cover the entire surface of the object, but the triplanar mapping confines visibility of the texture map onto the corresponding axes that are active for that texture. Figure 3 compares an image without the triplanar mapping versus one that is plugged into the Triplanar Map node\'s Positive X and Positive Y axis pins.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_246.png)       | Triplanar Comparision                         |
|                                   |                                               |
|                                   | ![](images/texturemaptriplanar3_1401x940.png) |
+-----------------------------------+-----------------------------------------------+

Figure 3: No triplanar mapping (left); triplanar mapping (right)

 

The Triplanar projection can localize the texture projection to a corresponding plane and allow texture UV transforms relative to that projection axis (figure 4).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_247.png)       | Texture Projection                           |
|                                   |                                              |
|                                   | ![](images/texturemaptriplanar4_702x992.png) |
+-----------------------------------+----------------------------------------------+

Figure 4: Texture projection connected to the Triplanar node

You can adjust the Triplanar Map\'s Blend Angle and Blend Cube Transform parameters to soften the seams (figure 5).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_248.png)       | Triplanar Blending                           |
|                                   |                                              |
|                                   | ![](images/texturemaptriplanar5_624x528.png) |
+-----------------------------------+----------------------------------------------+

Figure 5: Triplanar Map with Blend Angle and Blend Cube Transform adjustments
