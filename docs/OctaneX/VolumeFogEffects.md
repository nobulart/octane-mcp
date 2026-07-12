There are various ways to create fog in OctaneRender®. The simpliest method is to add  a Medium node to the Medium pin on the Daylight or Texture Environment node. In figure 1, A Volume Medium and a Scattering node are connected to a Medium Switch node to provide the ability to switch between each medium type connected to the Daylight Environment\'s Medium pin. The Post Processing Volume Effects can also produce fog effects with minimal effort. Please see the [Post-Processing Node](Post-ProcessingNode.md) topic for more information. 

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_466.png)       | Daylight Medium Nodes                             |
|                                   |                                                   |
|                                   | ![](images/Volume_Fog_Effects_Fig01_SE_v2023.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: Medium nodes connnected to the Medium pin on a Daylight Environment node

The disadvantage of this simple method is that it does not provide much control over the density of the fog volume from foreground to background. VDB nodes provide more control over the fog density with scene depth. The Volume node and the Unit Volume node found under the Geometry category in the Node Graph Editor can be used to generate VDB volumes. The Unit Volume node is a convenient way to add volume to the scene without having to import a VDB file from another appllication. In figure 2, a cube VDB has been inmported using the Volume node and a Unit Volume node has also been added. The nodes are attached to a Geometry Switch node so comparisions can be made between the two volume fog results. Figures 3 and 4 show a camparison between the imported VBD and the Unit Volume results.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_467.png)       | Unit Volume And VBD Nodes                       |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig02_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 2: Adding an imported VBD and a Unit Volume node using the Geometry Switch node

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_468.png)       | VDB Import                                      |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig03_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 3: The imported VBD result as volume fog

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_469.png)       | Unit Volume                                     |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig04_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 4: The Unit Volume result as a volume fog

There is no standard setting for using a VDB file because the settings depends a lot on the volume geometry\'s size, the most important attributes to tweak are the Density and the Volume Step Length. Check the maximum values for Absorption, Scattering, and Emission that is in the VDB itself. For the example above, those values are less than 0.2, 0.2, 0.2, respectively (figure 5).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_470.png)       | Import VDB Attributes                           |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig05_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 5: [Absorption](javascript:void(0);), Scattering, and Emission attributes

Considering the size (e.g., abs/scat/emis: 0.141,0.141,0.141) is important if you want to use some Absorption and Scattering ramps because the ramps will have a Max Value attribute and this should not be greater than the size of the imported volume (figure 6). This produces a more believeable and accurate fog result (figure 7).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_471.png)       | Volume Gradient Max Value                       |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig06_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 6: The Absorption and Scattering Volume Gradient settings

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_472.png)       | Volume Gradient Results                         |
|                                   |                                                 |
|                                   | ![](images/Volume_Fog_Effect_Fig07_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 7: The scene results from the settings in Figure 6
