The Texture blend node can be used to add an imported texture map or any of the procedural Octane textures to the compositing node tree (figure 1). 

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_542.png)       | Texture Blend Node                    |
|                                   |                                       |
|                                   | ![](images/Texture_Fig01_SE_2024.jpg) |
+-----------------------------------+---------------------------------------+

Figure 1: The Texture blend node used to import a checker pattern for the background in the compositing node tree

### Texture Parameters

Enabled - Determines whether the Texture node is active or not.

RGB Texture - Specifies the texture to be used which can be imported or procedural. 

RGB Sample Count - Determines the number of times to sample the RGB texture for each pixel.

Alpha Texture - Specifes the texture to be used for opacity, the default is a greyscale color.

Alpha Sample Count - Determines the number of times to sample the Alpha texture for each pixel.

UV Transform - Provides transformation parameters for the RGB texture.

Blending Settings - Determines the blending mode for the Texture node.
