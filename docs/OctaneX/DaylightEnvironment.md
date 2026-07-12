The Daylight Environment system simulates an outdoor lighting setup using real-world parameters. You can access it by right-clicking in the Nodegraph Editor, then navigating to the Environments category, and then clicking on Daylight Environment (figure 1).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_318.png)       | Daylight Environment                                |
|                                   |                                                     |
|                                   | ![](images/Daylight_Environment_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: Create a Daylight environment node

 

Switching to the Daylight environment can be done in the Node Inspector for the current Render Target as well (figure 2):

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_319.png)       | Daylight Environment in Node Inspector              |
|                                   |                                                     |
|                                   | ![](images/Daylight_Environment_Fig02_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 2: Changing the environment to the Octane Daylight System

 

### Daylight Environment Parameters

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_320.png)       | Daylight Environment Parameters                      |
|                                   |                                                      |
|                                   | ![](images/Daylight_Environment__Fig03_SE_v2023.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 3: The Daylight environment parameters in the Node Editor

Longitude/Latitude - Get realistic sun settings for the specified geographic location.

Month/Day/GMT Offset/Local Time - These parameters can accurately place the sun in the sky according to the date/time for the sun at the current longitude/latitude.

Interactive Map - The map can set the scene\'s geographic location. This lets you adjust the sun\'s position by dragging the crosshairs around on the map (Figure 3).

![](images/enviromentdaylightinteractivemapv15.png)

Figure 4: An interactive map can set the scene\'s location relative to the sunlight

Sky Turbidity - Adjusts the sunlight shadow\'s sharpness. Low values create sharp shadows similar to a sunny day, and higher values diffuse the shadows similar to a cloudy day.

Power - Adjusts the light\'s strength. This can affect the image\'s overall contrast and exposure levels.

Sun Intensity - Adjusts the scale factor for the sun and can be used to adjust the relative power of the sun compared to the sky.

North Offset - Adjusts the scene\'s actual North direction. This is useful for architecture visualization to ensure the sun\'s direction is accurate to the scene.

Daylight Model - Specifies the daylight model to use as the current environment.

- Octane Daylight - This is the new default daylight model simulates full-spectrum daylight, providing more sky color variation as the sun moves along and bearing shorter rays as the sun moves closer to the normal plane.
- Preetham Daylight - This is the old daylight model that lights a scene with basic spectral radiance as the sun moves over the horizon at a relative distance from the object.
- Nishita Daylight - Implements atmospheric scattering based on the Nishita sky model and displays the color variations, which are optical effects caused by the particles in the atmosphere.
- Hosek Wilkie Daylight - Produces more realistic and detailed results than other implementations specially in hazy conditions and near the horizon.

+----------------------------------------------------------------------------------------------------------+
| Note                                                                                                     |
|                                                                                                          |
| The Nishita sky does not work with sky color and sunset color given that it is a physically-based model. |
+----------------------------------------------------------------------------------------------------------+

Sky Color/Sunset Color - These settings are used by the New daylight model to customize the spectral shade of light. This can affect overall mood expressed by the image.

Sun Size - Controls the sun radius in the Daylight environment.

Ground Color - Base color of the ground. Only works with the New daylight model and Nishita Light Mode.

Ground Start Angle - The angle (in degrees) below the horizon where the transition to the ground color begins. This only works the the New sky model.

Ground Blend Angle - The angle above which the sky color transitions to the ground color. This only works with the New sky model.

Sky Texture - Connects a texture to use as the background, and ensures that objects in the scene accurately reflect it.

Importance Sampling - This toggles the Sky texture\'s importance sampling, similar to the Texture environment\'s importance sampling.

Cast Photons - If photon mapping is used, this will cast photons from bright areas in the environment map.

Medium - This parameter accepts an [Absorption](javascript:void(0);), [Scattering](javascript:void(0);), or Volume medium node to create volume/fog effects across the scene. For more information, see the [Volume Fog Effects](VolumeFogEffects.md) topic under the Effects Overview category in this manual.

Medium Radius - Adjusts the medium\'s scale.

Medium Light Pass mask - Enables or disables lights on the scattering environment medium.

Use in Post Volume - Enables or disables the light in post volume rendering.

#### Visible Environment

Backplate - Generates a cutout rendering where foreground elements are positioned in the scene.

Reflections - Generates the Planetary environment in scene object reflections.

Refractions - Generates the Planetary environment in scene object refractions.
