The Texture environment affects the environment\'s illumination and color. This node can add an [HDRI](javascript:void(0);) environment texture to the scene for illumination. You can access it by right-clicking in the Nodegraph Editor, navigating to the Environments category, and then choosing Texture Environment (figure 1).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_324.png)       | Texture Environment                                |
|                                   |                                                    |
|                                   | ![](images/Texture_Environment_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: Selecting the Texture environment option from the Nodegraph Editor

The Texture color swatch can scale from white to black as a uniform color for scene illumination (figure 2).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_325.png)       | Texture Color                                      |
|                                   |                                                    |
|                                   | ![](images/Texture_Environment_Fig02_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 2: Texture is used to shade the background illumination

You can use a [High Dynamic Range Image](javascript:void(0);) (HDRI) map as a texture environment. To use an HDRI file as the environment, connect an RGB Image node to a Texture Environment node\'s Texture pin, then load the image file when you\'re prompted (figure 3).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_326.png)       | HDRI Texture                                       |
|                                   |                                                    |
|                                   | ![](images/Texture_Environment_Fig03_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 3: Loading an RGB image as the texture

 

### Texture Environment Parameters

Texture - Specifies either a color using the [RGB Color](RGBRGBAColor.md) [](RGBRGBAColor.md) node or an HDR image using the [RGB Image](RGBImage.md) node. 

Power - Changes the HDRI image\'s brightness.

Importance Sampling - Enables quicker convergence (noise reduction) for HRDI images by applying importance to certain areas of the HDRI, which prioritizes areas to resolve sample rays more often than other areas.

Cast Photons - If photon mapping is used, this will cast photons from bright areas in the environment map.

Medium - This parameter accepts an [Absorption](javascript:void(0);), [Scattering](javascript:void(0);), or Volume medium node to create volume/fog effects across the scene. For more information, see the Volume Fog Effects topic under the Effects Overview category in this manual.

Medium Radius - Adjusts the medium\'s scale.

Medium Light Pass mask - Enables or disables lights on the scattering environment medium.

#### Visible Environment

Backplate - Generates a cutout rendering where foreground elements are positioned in the scene.

Reflections - Generates the Planetary environment in scene object reflections.

Refractions - Generates the Planetary environment in scene object refractions.

 

In some cases, shadows cast when using an HDR image in the Texture Environment node turn out too soft. In these situations, combine the HDR image with the Daylight Environment node instead of using the Texture Environment (Figure 4). Figure 5 shows a comparison between using the Texture Environment to light a scene and using Daylight Environment with an HDR image as the Sky texture.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_327.png)       | HDRI with Daylight Environment    |
|                                   |                                   |
|                                   | ![](images/environment.png)       |
+-----------------------------------+-----------------------------------+

Figure 4: Using a Daylight Environment node with an HDRI image as the Sky texture

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_328.png)       | HDRI with Daylight Environment    |
|                                   |                                   |
|                                   | ![](images/environment02.jpg)     |
+-----------------------------------+-----------------------------------+

Figure 5: Comparison of shadow quality between Texture Environment only (left) and Daylight Environment with a sky texture (right)
