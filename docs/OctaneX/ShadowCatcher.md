The [Shadow Catcher](javascript:void(0);) option can create shadows cast by objects onto the surrounding geometry. You can cast shadows on the ground plane as well as other surfaces of varying shapes. This feature is enabled by activating the Shadow Catcher option on either the [Diffuse](javascript:void(0);) or Universal materials applied to the shadow-catching surfaces (figure 1).

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_458.png)       | Activating Shadow Catcher                     |
|                                   |                                               |
|                                   | ![](images/Shadow_Catcher_Fig01_SE_v2021.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: A Model is integrated into an image using the Shadow Catching material

In the Render Kernel window, activate [Alpha Channel](javascript:void(0);) and disable Keep Environment. When the image renders, the shadows appear over the transparent parts of the surface. This image can work in a compositing package to merge the object and the shadows into the composition.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_459.png)       | Alpha and Keep Environment                    |
|                                   |                                               |
|                                   | ![](images/Shadow_Catcher_Fig02_SE_v2021.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 3: Activating the Alpha and deselecting the Keep Environment checkboxes in the Render Kernel settings
