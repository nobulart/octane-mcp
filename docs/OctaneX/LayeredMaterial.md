The Layered material node constructs complex materials that consist of a base layer and up to eight [Material](javascript:void(0);) Layers. You can create complex materials in a physically-based manner, as opposed to manually [mixing materials](javascript:void(0);) together. By default a Diffuse material is listed as the base material. Other materials can be selected as the base material. 

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_92.png)        | Layered Material                                |
|                                   |                                                 |
|                                   | ![](images/Layered_Material_Fig01_SE_v2021.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: Layered material node parameters

 

### Layered Material Parameters

Add Layer - Adds a new Layer input to the end of the Node. You can add up to eight Layer inputs.

Base Material - The material that sits below any additional Material Layers.

Layer 1-8 - The Material Layer inputs.

With the Layered material, you are given all Material Layers used in OctaneRender®, allowing you to reconstruct pre-existing Octane materials or your own uber-material.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_633.png)       | Layered Material Example                   |
|                                   |                                            |
|                                   | ![](images/LayeredMaterial_example_01.png) |
+-----------------------------------+--------------------------------------------+

Figure 2: Recreating the [Glossy](javascript:void(0);) Material by using a [Diffuse material](javascript:void(0);) and a [Specular](javascript:void(0);) layer

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_634.png)       | Layered Material Example                   |
|                                   |                                            |
|                                   | ![](images/LayeredMaterial_example_02.png) |
+-----------------------------------+--------------------------------------------+

Figure 3: Recreating the Metallic material by using a [Diffuse](javascript:void(0);) material and Metallic layer

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_635.png)       | Layered Material Example                   |
|                                   |                                            |
|                                   | ![](images/LayeredMaterial_example_03.png) |
+-----------------------------------+--------------------------------------------+

Figure 4: A simple [PBR](javascript:void(0);) metallic/roughness workflow
