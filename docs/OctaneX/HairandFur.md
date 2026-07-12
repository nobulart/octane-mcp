OctaneRender® can import and render hair or fur geometry. OctaneRender retrieves hair and fur data from an [Alembic](javascript:void(0);) file, which may include a strand thickness value or a gradient attribute. If the file doesn\'t have a thickness value or gradient attribute, OctaneRender respectively creates the hair gradient attribute and bases the strand thickness according to the default value set in the Import Preferences dialog (figure 1).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_454.png)       | Alembic Hair Preferences                    |
|                                   |                                             |
|                                   | ![](images/Hair_And_Fur_Fig01_SE_v2023.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 1: Setting Default Hair Thickness and Default Hair Gradient Interpolation values

The Alembic file may come from different 3D modeling applications, and it may contain geometry derived from the application's native hair primitive in the form of hair guides. The hair guides are then exported for use in OctaneRender in conjunction with its proxy system for replicating and scattering the hair guides to create custom hair and fur effects. You can also generate hair or fur with third-party geometry scatter plugins, such as Ornatrix. When you import the Alembic file into OctaneRender, the geometry that appears are the hair guides.

+-----------------------------------+------------------------------------------+
| ![](images/NewItem_455.png)       | Hair Guides                              |
|                                   |                                          |
|                                   | ![](images/Hair_Fur_Fig02a_SE_v2020.jpg) |
+-----------------------------------+------------------------------------------+

Figure 2: Hair guides

You can instance the hair guides by using OctaneRender's instancing and scattering features without using too much [GPU](javascript:void(0);) memory. For more information, see the [Instancing](UsingInstances.md) topic in this manual. You can also use a CSV file as input for the transforms in a Scatter node (Figure 3). For more information, see the [Scattering](Scatter.md) topic in this manual.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_456.png)       | Scatter                           |
|                                   |                                   |
|                                   | ![](images/HairAndFurFig7.png)    |
+-----------------------------------+-----------------------------------+

Figure 3: Scatter node settings

The material is then further improved by using a W Coordinate texture in conjunction with a Gradient Map node, allowing you to place a gradient for each strand (Figure 4).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_457.png)       | W Coordinate Gradient Map                   |
|                                   |                                             |
|                                   | ![](images/Hair_And_Fur_Fig04_SE_v2022.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 4: Applying the W Coordinate to a hair system.

Additionally, a new hair m[aterial](javascript:void(0);) node has been added for even more control over hair and fur rendering. For more information on the Hair Material node, please refer to the [Hair Material](HairMaterial.md) article under the [Materials](javascript:void(0);) topic in this manual
