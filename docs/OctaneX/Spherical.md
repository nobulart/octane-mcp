The Spherical projection is used for Environment textures and [IES](javascript:void(0);) light distributions. It performs latitude-longitude mapping for the U and V coordinates. When used with Procedural textures, the W coordinate is the distance from the origin (Figure 1).

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_302.png)       | Spherical                                             |
|                                   |                                                       |
|                                   | ![](images/Spherical_Projection_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: The Spherical projection used with the Checks procedural texture

 

When using an Image texture to light a scene with the OctaneRender® Environment node, spherical mapping combined with a Transforms node lets you rotate and translate the environment sphere\'s texture. To rotate a texture image (e.g., an HDR image) around a vertical axis, switch the texture environment image\'s projection to Spherical and rotate it via the Y axis through the Sphere Transformation sliders. The Use Rest Attribute option keeps texture maps from distorting when the geometry is animated. 

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_303.png)       | Various Spherical PRojections                |
|                                   |                                              |
|                                   | ![](images/projectionsspherical_717x358.png) |
+-----------------------------------+----------------------------------------------+

Figure 2: Spherical projection applied to a box, cylinder, and sphere
