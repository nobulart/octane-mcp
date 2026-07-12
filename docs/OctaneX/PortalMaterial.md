[Portal](javascript:void(0);) materials optimize rendering light sources by helping the render kernel find important light sources in the scene. For example, interior scenes illuminated by an outside light source that comes through windows can be difficult for the path tracer to optimize the light as it enters the interior environment. To help the path tracer find these light sources, you can put a polygon plane outside the window, and then apply a Portal material to the plane to create a portal plane. This setup improves the light quality and increases the render efficiency.

 

To set up a scene using Portal materials, make sure that every window or opening in the environment is covered by a portal plane. It will not work if only one window has a portal over it when all other windows do not have a portal over them. And the normal direction of the portal plane should be facing inwards towards the interior, or the scene will not render properly. Don\'t block portal planes with other geometry like glass surfaces. Objects with the Portal material applied are invisible as geometry in the rendering.

We recommend using the least amount of geometry for Portals. A few simple rectangular planes are best, as dense geometry used for portal planes can slow down rendering. It is possible to use a single piece of portal geometry to cover several openings such as multiple windows on a single wall. However, if the geometry is too large, that can reduce rendering efficiency. It\'s important to strike a balance between an opening\'s coverage and the size of the geometry that uses the Portal material.

Use Portal materials with the Pathtracing and PMC kernels, as it will not work when rendering with the Direct Light kernel.

The two images in Figure 1 show the rendering results with and without a Portal material. The scene shows a glass sphere rendered in a room lit by light coming through a window. The scene is rendered using 500 samples. The first image does not have a portal plane placed over the opening, and it is noisier than the second image, which does have a portal plane.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_107.png)       | Portal Comparison                              |
|                                   |                                                |
|                                   | ![](images/Portal_Material_Fig01_SE_v2023.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: Two images rendered without and with a portal plane
