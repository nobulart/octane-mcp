The [Black Body](javascript:void(0);) emission uses Temperature (in Kelvin) and Power to control the color and intensity of the light, respectively (figure 1). 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_332.png)       | Black Body Emission                       |
|                                   |                                           |
|                                   | ![](images/Black_Body_Fig01_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: A Black Body emission node connected to the Emission pin on a Diffuse material

### Black Body Emission Parameters

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_333.png)       | Black Body Parameters                     |
|                                   |                                           |
|                                   | ![](images/Black_Body_Fig02_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: Black Body emission parameters

Texture - Sets the light source\'s efficiency to either a value or texture. Keep in mind that real-world lights aren\'t 100% efficient at delivering power at their specified wattage - a 100-watt light bulb doesn\'t deliver 100 watts of light. This parameter enters the real-world values.

Power - The light source\'s wattage. You should set each light to their real-world wattage - for example, set a desk lamp to 25 watts, a ceiling lamp to 100 watts, and an LED light to 0.25 watts.

Surface Brightness - Causes emitters to keep a constant Surface Brightness, independent of the emitter\'s surface area.

Keep Instance Power - Enabling this option with Surface Brightness disabled and Uniform Scaling applied to the object causes Power to remain constant.

Double Sided - Allows emitters to emit light from the front and back sides.

+-----------------------------------+-------------------------------------------------------------------------------------+
| ![](images/NewItem_334.png)       | Double Sided                                                                        |
|                                   |                                                                                     |
|                                   | ![](images/Double-Sided-ON-CAPTIONED.png)![](images/Double-Sided-OFF-CAPTIONED.png) |
+-----------------------------------+-------------------------------------------------------------------------------------+

Figure 3: Example of Double Sided option enabled

Temperature - The temperature (in Kelvin) of the Black Body emission\'s light.

Normalize - Ensures all normal vectors have the same length for the Black Body emission - this keeps the emitted light\'s luminance constant if the temperature varies. this is enabled by default.

Distribution - Controls the light pattern. You can set this to a Greyscale or RGB image so that you can load an Image texture or [IES](javascript:void(0);) file. the Image texture\'s Projection nodes adjust the light\'s orientation and direction.

Sampling Rate - Choose what light sources receive more samples.

Light Pass ID - The Light Pass ID captures the respective emitter\'s contribution.

Visible On [Diffuse](javascript:void(0);) - Enables light source visibility on diffuse surfaces. Black Body or Texture emission light sources can cast illumination or shadows on diffuse objects. Disabling this option disables emission - it\'s invisible in diffuse reflections, but is still visible on specular reflections. It\'s also excluded from the Direct light calculation. This option is enabled by default.

+-----------------------------------+-----------------------------------------------------------------------------------+
| ![](images/NewItem_335.png)       | Visible on Diffuse                                                                |
|                                   |                                                                                   |
|                                   | ![](images/Visible-ALL-CAPTION.png)![](images/Visible-on-Diffuse-OFF-CAPTION.png) |
+-----------------------------------+-----------------------------------------------------------------------------------+

Figure 4: Visible On Diffuse enabled (left) and disabled (right)

Visible On [Specular](javascript:void(0);) - Enables the light source\'s visibility on specular surfaces, and hides emitters on specular reflections/refractions. This is enabled by default.

+-----------------------------------+------------------------------------------------------------------------------------+
| ![](images/NewItem_336.png)       | Visible on Specular                                                                |
|                                   |                                                                                    |
|                                   | ![](images/Visible-ALL-CAPTION.png)![](images/Visible-on-Specular-OFF-CAPTION.png) |
+-----------------------------------+------------------------------------------------------------------------------------+

Figure 5: Visible On Specular enabled (left) and disabled (right)

Visible on Scattering Volumes - If enabled, the illumination is visible on scattering volumes.

Transparent Emission - Light sources cast illuminations on diffuse objects, even if the light source is on transparent material.

+-----------------------------------+-----------------------------------------------------------------------------------------------------+
| ![](images/NewItem_337.png)       | Transparent Emission                                                                                |
|                                   |                                                                                                     |
|                                   | ![](images/Transparent_Emission_B-ON-CAPTION.png)![](images/Transparent_Emission_B-OFF-CAPTION.png) |
+-----------------------------------+-----------------------------------------------------------------------------------------------------+

Figure 5: Comparison between Transparent Emission on and off

Cast Shadows - Enables light sources to cast light and shadows on diffuse surfaces, letting you disable direct light shadows for Mesh emitters. To make this option work, the Direct light calculation must include the emitter (the sampling rate must be greater than 0). This option is enabled by default.

+-----------------------------------+---------------------------------------------------------------------------------+
| ![](images/NewItem_338.png)       | Shadow Casting                                                                  |
|                                   |                                                                                 |
|                                   | ![](images/Cast_Shadows-ON-CAPTION.png)![](images/Cast_Shadows-OFF-CAPTION.png) |
+-----------------------------------+---------------------------------------------------------------------------------+

Figure 7: Cast Shadows enabled (left) and disabled (right)
