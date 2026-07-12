The Directional light functions are an infinitely distance light source and creates an effect much like the sun illuminating on the surface of the earth. Rotation is the only transform value that will affect this light type since it originates from an infinite location (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_347.png)       | Directional Light                                |
|                                   |                                                  |
|                                   | ![](images/Directional_Light_Fig01_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: The Directional light type and it\'s assocated parameters

### Directional Light Parameters

Texture - Sets the light source\'s efficiency. You can set this to a value or texture. Keep in mind that real-world lights aren\'t 100% efficient at delivering power at their specified wattage - a 100-watt light bulb doesn\'t deliver 100 watts of light. This parameter enters the real-world values.

Power - The light source\'s wattage. You should set each light to their real-world wattage - for example, set a desk lamp to 25 watts, a ceiling lamp to 100 watts, and an LED light to 0.25 watts.

Surface Brightness - Causes emitters to keep a constant Surface Brightness, independent of the emitter surface area.

Keep Instance Power - Enabling this option with Surface Brightness disabled and Uniform Scaling applied to the object causes Power to remain constant.

Double Sided - Allows emitters to emit light from the front and back sides.

Distribution - Controls the light pattern. You can set this to a Greyscale or RGB image so that you can load an Image texture or [IES](javascript:void(0);) file. the Image texture\'s Projection nodes adjust the light\'s orientation and direction.

Sampling Rate - Choose what light sources receive more samples.

Light Pass ID - The Light Pass ID captures the respective emitter\'s contribution.

Visible on Diffuse - Enables light source visibility on diffuse surfaces. It enables [Black Body](javascript:void(0);) or Texture emission light sources to cast illumination or shadows on diffuse objects. Disabling this option disables emission - it\'s invisible in diffuse reflections, but is still visible on specular reflections. It\'s also excluded from the Direct light calculation. This option is enabled by default.

Visible on [Specular](javascript:void(0);) - Enables the light source\'s visibility on specular surfaces, and hides emitters on specular reflections/refractions. This is enabled by default.

Visible on [Scattering](javascript:void(0);) Volumes - If enabled, the light source is visible on scattering volumes.

Transparent Emission - Allows light sources to cast illumination on diffuse objects, even if the light source is on transparent material.

Cast Shadows - Enables light sources to cast light and shadows on diffuse surfaces, letting you disable direct light shadows for Mesh emitters. To make this option work, the Direct light calculation must include the emitter (the sampling rate must be greater than 0). This option is enabled by default.

Light Transform - The only parameter in this rollout that affects the light source is Rotation since the light source is infinite.

Light Sample Spread Angle - Larger value will create a larger light source, as a result, the shadows will become softer. 

Use in Post Volume - Enables or disables the light in post volume rendering.
