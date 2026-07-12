The Volume to Texture node provides a way to convert an imported VBD file into texture map data (figure 1). There is an additional Grid ID parameter that determines what data from the incoming VBD file will be used to generate the texture map.

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_209.png)       | Volume to Texture                                |
|                                   |                                                  |
|                                   | ![](images/Volume_To_Texture_Fig01_SE_v2021.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: An imported VBD file used to generate texture map information

### Volume to Texture Parameters

VDB - Specifies the VDB fiel to import.

P Transform - Determines the position coordinate transform.

Projection - Specifies the projection type to use with the VDB file. 

Grid ID - Specifies which grid to read from the connected VDB file. 

Grid Name - If Use Grid Name is selected in the Grid ID, the grid name is specified here.
