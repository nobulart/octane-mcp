The Falloff Map texture controls material blending, depending on the viewing angle of the material\'s geometry (figure 1).

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_215.png)       | Falloff Map                                          |
|                                   |                                                      |
|                                   | ![](images/Falloff_Map_Texture_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 1: The Falloff Map texture used to control the blending of two RGB Color nodes connected to a Mix Texture node

The angle between the Eye Ray and the Shading Normal is mapped from \[0°, 90°\] to \[0, 1\]. For values larger than 1, the Falloff node does a gamma correction using the Falloff Skew Factor as an exponent. OctaneRender® uses the Skew Factor to interpolate between the spectral shades resulting from the Minimum Value and Maximum Value parameters, which are based on the first and second inputs of a Mix node.

You can use the Falloff Map to control the Mix node\'s Amount parameter. The Mix node can either be Mix Texture or Mix [Material](javascript:void(0);).

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_656.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg4_661x384.png) |
+-----------------------------------+--------------------------------------------+

Figure 2: Falloff Map connected to a Mix Texture node

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_657.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg5_733x307.png) |
+-----------------------------------+--------------------------------------------+

Figure 3: Falloff Map connected to a [Mix Material](javascript:void(0);) node

 

### Falloff Map Parameters

#### Falloff Map Modes

Normal vs. Eye Ray - This is the default mode where OctaneRender® calculates the falloff from the angle between the Surface Normal and the Eye Ray. This mode is often used for reflections. The Falloff color range affects faces directly in front of the view, and gradually falls at angled faces towards the sides as it falls away from the straight-on viewing angle. The Falloff Direction parameter does not apply.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_658.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg6_724x351.png) |
+-----------------------------------+--------------------------------------------+

Figure 4: Skew factor = 1; Direction does not apply

Normal vs. Vector 90deg - OctaneRender® calculates the falloff from the angle between the Surface Normal and the specified direction vector, maxing out at 90 degrees. This is similar to the default mode, except that it maintains the effect of the color range according to the Falloff Direction parameter.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_659.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg7_723x351.png) |
+-----------------------------------+--------------------------------------------+

Figure 5: Skew factor = 1; Direction x = 1

 

Normal vs. Vector 180deg - OctaneRender® calculates the falloff from the angle between the Surface Normal and the specified direction vector, maxing out at 180 degrees. This provides a wider color range from the minimum to the maximum values, and maintains the effect of the color range according to the Falloff Direction parameter.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_660.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg8_720x350.png) |
+-----------------------------------+--------------------------------------------+

Figure 6: Skew factor = 1; Direction x = 1

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_661.png)       | Falloff Map                                |
|                                   |                                            |
|                                   | ![](images/fallofftextureimg3_701x176.png) |
+-----------------------------------+--------------------------------------------+

Figure 7: Falloff Map parameters

 

Apply Bump/Normal Map - If enabled, the shading normal, which includes bump/normal mapping, will be used to calculate the falloff. If disabled, the smooth normal, which does not include bump/normal mapping, will be used instead. 

Minimum Value - The visible material on the surface facing the camera. A value of 0 displays the material connected to Material pin 2, and a value of 1 displays the material connected to Material pin 1.

Maximum Value - Determines what material displays towards the grazing angles. A value of 0 displays the material connected to Material pin 2, and a value of 1 displays the material connected to Material pin 1.

Falloff Skew Factor - Balances the Normal and Grazing angles\' influence. Low values result in stronger Grazing angle influence - any textures that the Maximum Value controls cover more surface. High values result in stronger Normal angle influence - any textures that the Minimum Value controls cover more surface.

In the figure below, a red [Diffuse material](javascript:void(0);) connects to the Mix material\'s first Material pin, and a white [Diffuse](javascript:void(0);) material connects to the second Material pin. The Falloff map then connects to the Mix material\'s Amount pin.

 

A value of 0.1 leads to almost complete coverage by the grazing value regardless of viewing angle, whereas a value of 15 leads to almost complete coverage by the Normal value. This parameter\'s default setting is 6.

While the index value on [Glossy](javascript:void(0);) and [Specular](javascript:void(0);) nodes corresponds to a real-world Index of Refraction (IOR) value on dielectric materials like plastic and glass (OctaneRender® doesn\'t yet support metals and Bezier curves), the Falloff node works differently because of this Falloff Skew Factor. If set to 1, then the value is proportional to the angle between the Normal and the Camera Ray. For example, if view angle is 45°, then the value is 0.5. If the value is larger than 1, then it applies a power curve to the angle. If the value is smaller than 1, then it inverts the skew factor, and mirrors the power curve.

- - falloff ≤ 1 : y = x falloff
  - falloff ≥ 1 : y = 1 -- (1 -- x) (1 / falloff )

 

#### Falloff Direction

This is used by the Normal vs. Vector 90deg and Normal vs. Vector 180deg modes. For most materials, the Fresnel effect (the default mode) is often correct, while Falloff Direction applies for exceptional cases, which can adjust relative to the camera. Changing the object rotation will not change the Falloff Direction orientation.

You can approximate the behavior of glass with a Skew Factor of 8.0 and a Normal value of 0.034.

![](images/falloffmap_fig10_SEv4-0.png)

Figure 8: Falloff Direction curves

You can also use the Falloff Map for other things, like the input for glass opacity. Falloff is useful for car shaders, water shaders, and fabrics like velvet. It is also useful for some metals to simulate some coating effects.

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_662.png)       | Falloff Map                                 |
|                                   |                                             |
|                                   | ![](images/fallofftextureimg11_885x371.png) |
+-----------------------------------+---------------------------------------------+

Figure 9: Car shader example
