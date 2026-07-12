The Cosine Mix texture mixes two textures together according to a cosine wave. In Figure 1, a Checks texture combines with a Marble texture using a Cosine Mix texture, and then it connects to a [Diffuse](javascript:void(0);) material\'s Diffuse channel. It is very similar to the Mix texture, but the difference between the Cosine mix texture and the Mix texture is more apparent when the Mix Amount parameter is shifted towards 0 or 1.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_261.png)       | Cosine Mix Texture                                |
|                                   |                                                   |
|                                   | ![](images/Cosine_Mix_Texture_Fig01_SE_v2022.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: A Marble texture is blended with a Checks texture using the Cosine Mix texture

 

The parameters of the Cosine Mix texture consist of the inputs for the two textures, and the Mix Amount parameter. The Mix Amount parameter accepts a float value or any texture that outputs a float, such as a Greyscale Image texture.
