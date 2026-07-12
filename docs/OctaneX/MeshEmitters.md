A Mesh Emitter is a polygon object that emits light into a scene. This is possible by applying a [Diffuse](javascript:void(0);), Universal, or Standard Surface material to the Mesh object, and then connecting a [Black Body](javascript:void(0);) or Texture emission node to the material\'s Emission channel (figure 1).

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_330.png)       | Mesh Emitting Object                         |
|                                   |                                              |
|                                   | ![](images/Mesh_Emitters_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: A light-emitting [Diffuse material](javascript:void(0);)

 

To use a Mesh as a light source, apply a Diffuse, Universal, or Standard Surface material to the surface, then connect an Emission node to the Emission pin. There are two types of [Emissions](javascript:void(0);):

- Black Body Emission - Uses Color Temperature (in Kelvin) and Power to control the light\'s color and intensity, respectively.
- Texture Emission - This allows any valid Texture type to set the light intensity. You can use this Emission to create interesting effects, such as TV screens, by using an Image texture as the source.
- Emission Swtich - This node allows for two or more emission nodes to be connected to an emission input pin.

You can access the emission types by right-clicking in the Nodegraph Editor and navigating to the Emission category.

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_331.png)       | Mesh Emitter Nodes                           |
|                                   |                                              |
|                                   | ![](images/Mesh_Emitters_Fig02_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 2: Selecting an Emission node from the Nodegraph Editor context menu

+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                  |
|                                                                                                                                                                                                                       |
| When opening scenes built with OctaneRender® v3.06 and earlier, you will need to adjust some values in the emission nodes due to significant changes and improvements built in recent versions affecting these nodes. |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
