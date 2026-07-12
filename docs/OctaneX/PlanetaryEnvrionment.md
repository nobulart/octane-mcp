The Planetary environment is a flexible Nishita sky model. It is useful when rendering scenes set in outer space. For its effects to be visible, the camera has to have a very high altitude as it moves to outer space to view the expansive horizon of the planetary body. It takes into account the conditions within and beyond the atmosphere of a planetary body and its surroundings in space. Instead of a single ground color and a sky or sunset color, there is a planetary surface that reflects and emits light. This node extends the environment\'s medium (volume rendering and subsurface scattering) with an atmospheric scattering through the planetary body\'s atmosphere. Here, the atmosphere is perceived as a layer of gas surrounding a planetary mass. It is held in place because of gravity, so as the light travels into atmosphere either from the outer layer to the ground or from a light source within the atmosphere, then the atmosphere\'s density is sampled along the ray at regular intervals, resulting in an amount of scattering based on the atmosphere\'s density. This atmospheric scattering is based on the Nishita Sky model, which displays the variations of color that are optical effects caused by the particles in the atmosphere.

This environment is not connected to the camera, so you can zoom the camera in and out of the scene without affecting the environment\'s position in the scene. It gathers optical depth (transmittance) from the sun position, so if the sun position is greater than 0.0f on the Y-axis (upward direction), then it will be colored. If you put it below the horizon (less than 0.0f on the T-axis), then it won\'t gather transmittance, making it invisible.

You can access this environment node by right-clicking in the Nodegraph Editor, then navigating to the Environments category, and then clicking on Planetary Environment (figure 1).

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_321.png)       | Planetary Environment                                |
|                                   |                                                      |
|                                   | ![](images/Planetary_Environment_Fig01_SE_v2023.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 1: Accessing the Planetary Environment node from the Node Graph Editor window

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_322.png)       | Planetary Environment High Altitude                  |
|                                   |                                                      |
|                                   | ![](images/Planetary_Environment_Fig02_SE_v2023.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 2: Image rendered using the Planetary Environment with the camera set at a very high altitude

 

### Planetary Environment Parameters

Longitude/Latitude - Get realistic sun settings for the specified geographic location.

Month/Day/GMT Offset/Local Time - These parameters can accurately place the sun in the sky according to the date/time for the sun at the current longitude/latitude.

Sky Turbidity - Adjusts the sunlight shadow\'s sharpness. Low values create sharp shadows similar to a sunny day, and higher values diffuse the shadows similar to a cloudy day.

Power - Adjusts the overall strength of the Planetary Environment\'s illumination.

Sun Intensity - Scale factor that is applied to the sun only, used to adjust the relative power of the sun compared to the sky. Note: Values other than 1.0 can produce unrealistic results.

North Offset - Adjusts the scene\'s actual North direction. This is useful for architecture visualization to ensure the sun\'s direction is accurate to the scene.

Sun Size - Controls the size of the sun given as a factor of the actual sun diameter.

Altitude - The camera\'s altitude. Set this to a very high value in order to view the expansive horizon of the planetary body.

Star Field - Texture that conveys star fields behind the planet.

Importance Sampling - This toggles the Sky texture\'s importance sampling, similar to the Texture environment\'s importance sampling.

Cast Photons - If photon mapping is used, this will cast photons from bright areas in the environment map.

Medium - This parameter accepts an [Absorption](javascript:void(0);), [Scattering](javascript:void(0);), or Volume medium node to create volume/fog effects across the scene. For more information, see the [Volume Fog Effects](VolumeFogEffects.md) topic under the Effects Overview category in this manual.

Medium Radius - Adjusts the medium\'s scale.

Medium Light Pass mask - Enables or disables lights on the scattering environment medium.

Latitude - The latitude coordinate of the camera\'s current position.

Longitude - The longitude coordinate of the camera\'s current position.

### Planetary Surface Parameters

Ground Albedo - Color or texture map applied to the planetary surface.

Ground Reflection - The specular texture map on the planet.

Ground Glossiness - The planetary glossiness.

Ground Emission - The planet\'s surface texture map at nighttime.

Ground Normal Map - Normal map on the planet.

Ground Elevation - Elevation map on the planet.

### Visible Environment

Backplate - Generates a cutout rendering where foreground elements are positioned in the scene.

Reflections - Generates the Planetary environment in scene object reflections.

Refractions - Generates the Planetary environment in scene object refractions.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_323.png)       | Planetary Environment Example                   |
|                                   |                                                 |
|                                   | ![](images/PlanetaryEnvironment_Fig3_v4rc7.png) |
+-----------------------------------+-------------------------------------------------+

Figure 3: Image rendered using the Planetary environment with a starfield and texture map applied to the Ground Albedo
