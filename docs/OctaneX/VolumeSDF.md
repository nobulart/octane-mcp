The Volume SDF node acts as a placeholder for volume geometry ([VDB](javascript:void(0);)). It is different from a simple Volume node, which depends on traditional triangulated volumetric shaders. The Volume SDF node rebuilds a Signed Distance Field (SDF) based on the surface level sets defined in the VDB file, and recreates the mathematical description of the geometry instead. The new Volume SDF takes the same resolution as the original volume, but these can feed into OSL shaders, which allow the Volume SDF to take on an infinite resolution and even appended with procedural effects (Figure 3).

To use the Volume SDF node, right-click on the Nodegraph Editor, then click on Geometry, followed by Volume SDF (figure 1). From the operating system\'s File Explorer, select and import the volume VDB file as a Volume SDF.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_78.png)        | Volume SDF                                |
|                                   |                                           |
|                                   | ![](images/Volume_SDF_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: Adding the Volume SDF node to the scene

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_613.png)       | Volume VS Volume SDF                     |
|                                   |                                          |
|                                   | ![](images/VolumeSDF_fig2_SEv2018-1.png) |
+-----------------------------------+------------------------------------------+

Figure 2: Comparison of the original Volume node and the Volume SDF node

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_614.png)       | OSL with Procedural Effects            |
|                                   |                                        |
|                                   | ![](images/VolumeSDF_fig3_v2018-1.png) |
+-----------------------------------+----------------------------------------+

Figure 3: A modified OSL texture node that adds procedural effects to level set surfaces

### Applications Of SDF Surfaces And The Vectron Primitive

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_617.png)       | SDF Smooth Union                        |
|                                   |                                         |
|                                   | ![](images/VolumSDF_fig4_SEv2018-1.png) |
+-----------------------------------+-----------------------------------------+

Figure 4: An example of an SDF smooth union with a [Material](javascript:void(0);) mix implemented as part of the union

OctaneRender® will render SDF surfaces defined using OSL shaders without needing to convert them to a Mesh first. You can change the surfaces with input variables without having to wait for any processing, and you can also create networks of set operations such as unions, subtractions, intersection, and their smooth variants - none of which need to be meshed before rendering, and all are compiled using OSL.

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_618.png)       | Input Variables                          |
|                                   |                                          |
|                                   | ![](images/VolumeSDF_fig5_SEv2018-1.png) |
+-----------------------------------+------------------------------------------+

Figure 5: Example of OSL shaders with input variables to manipulate the shape of Vectron objects

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_619.png)       | Multiple Set Operations                  |
|                                   |                                          |
|                                   | ![](images/VolumeSDF_fig6_SEv2018-1.png) |
+-----------------------------------+------------------------------------------+

Figure 6: Example a more complex network of set operations (unions, subtractions, intersection, and their smooth variants)

 

You can download the example of the VolumeSDF Node in Figure 4 here: [sdf-union-material4.orbx](https://render.otoy.com/downloads/65/99/71/bb/sdf-union-material4.orbx)
