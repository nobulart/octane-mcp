Toon shading is a non-photorealistic way of depicting lighting effects (figure 1). While it still shows lighting effects, it does so in a simpler way, often with large areas of flat shaded color. In OctaneRender®, toon shading is controlled by Toon materials and light sources. Toon rendering in OctaneRender consists of two parts: a diffuse part, and a glossy highlight. The amount of detail in the shading is controlled using a Toon Ramp (Figure 2).

+-----------------------------------+---------------------------------------------------------+
| ![](images/NewItem_461.png)       | Diffuse and Glossy                                      |
|                                   |                                                         |
|                                   | ![](images/toonshading_colorpartscompare_SEv3-08-4.png) |
+-----------------------------------+---------------------------------------------------------+

Figure 1: Toon rendering consists of a diffuse part and a glossy highlight

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_460.png)       | Toon Ramp                                  |
|                                   |                                            |
|                                   | ![](images/Toon_Shading_Fig02_SE_2023.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 2: The amount of detail in the shading is controlled with a Toon Ramp

The Toon Material and Toon Ramp can be accessd in hte Node Graph Editor window under the Materials category (figure 3).

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_462.png)       | Toon Nodes                                 |
|                                   |                                            |
|                                   | ![](images/Toon_Shading_Fig03_SE_2023.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 3: Accessinng the Toon [Material](javascript:void(0);) and Toon Ramp

 

Toon shading uses its own light sources, independent from any Mesh emitters in the scene. This is done because with area lights you can never render sharp boundaries between different colors in the toon shader. Toon lights are not visible in the rendered image. There are two kinds of toon lights: Toon Point light (Figure 4), and Toon Directional light (Figure 5).

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_463.png)       | Toon Point Light                                  |
|                                   |                                                   |
|                                   | ![](images/toonshading_pointlights_SEv3-08-4.png) |
+-----------------------------------+---------------------------------------------------+

Figure 4: Point lights behave similar to small mesh lights

+-----------------------------------+---------------------------------------------------------+
| ![](images/NewItem_464.png)       | Toon Directional Light                                  |
|                                   |                                                         |
|                                   | ![](images/toonshading_directionallights_SEv3-08-4.png) |
+-----------------------------------+---------------------------------------------------------+

Figure 5: Directional lights behave similar to sunlight

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_465.png)       | Node Graph                                    |
|                                   |                                               |
|                                   | ![](images/toonshading_connect_SEv3-08-4.png) |
+-----------------------------------+-----------------------------------------------+

Figure 6: Basic Nodegraph showing the connections of Toon nodes used for Toon rendering

To control shadow color and brightness, go to Kernel Settings and use the Toon Shadowing pin.
