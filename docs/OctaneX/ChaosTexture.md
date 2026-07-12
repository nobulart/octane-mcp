The Chaos Texture node randomly scatters an input texture over a surface or UV space (figure 1). This node can be used to hide seams of image textures not intended for seamless use.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_252.png)       | Chaos Texture                                  |
|                                   |                                                |
|                                   | ![](images/Chaos_Texture_Fig01_SE_v2020_2.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: Using the Chaos Texture node to randomly place a texture map across the surface of a plane.

 

### Chaos Texture Parameters

 

Texture - This is the slot where textures are assigned. Procedural textures produce some interesting results.

Texture Projection - The projection type used for the texture.

Texture Transform - The transormation type used for the texture.

Grid Scale - Determines the size of the tiles.

Enable Grid Deformation - Enables randomization of the tile edges.

Grid Deformation Texture - A greyscale texture used to deform the tile edges. 

Grid Deformation Weight - Magnatude of the bias coming from the deformation texture. 

Grid Noise Transform - Rotation, scale, and translation of the internal noise used to deform the grid. 

Grid Noise Weight - Magnitude of the bias coming from the internal noise used to deform the gird. 

Grid Noise Seed - Seed to randomize the internal noise used to deform the grid. 

Mapping Seed - Seed used to randomize the area of the source texture used for each tile. 

Coverage - Controls the area of the source texture from which the tiles are sourced. If the source texture is not self-tiling, lower this vaule to avoid seeing UV boundary seams. If the value is too small, self-similarities in the output will be more apparent. 

Tile Transform - Transform of the UV space at the tile level. 

Enable Random Rotation - Enables rotation randomization at the tile level. 

Random Rotation Seed - Seed used for the random rotation of tiles. 

Random Rotation Range - Maximum amount of rotation applied to individual tiles. 

Random Rotation Steps - Number of possible values taken by the random rotation over the range. A vaule of 0 disables stepped rotation. 

Enable Blending - Enables blending between tiles.

Blending Exponent - Controls the exponent for exponentiated blending. 

Histogram Invariant Blending - Sets the output texture histogram cloaser to the histogram of the input. This option is only compatible with LDR images. 

Resolution - The resolution used to sample the input texture. This option is only used if the source texture is not an image or if the histogram invariant blending is enabled. 

Show Tile Structure - Displays the tile structure.

Show Hexagonal Tiling - Displays the hexagonal tiling.
