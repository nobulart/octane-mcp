The Add Glare Output AOV node can be used to add a glare around light sources in a composite node tree (figure 1).

+-----------------------------------+-----------------------------------------+
| ![](images/NewItem_568.png)       | Add Glare                               |
|                                   |                                         |
|                                   | ![](images/Add_Glare_Fig01_SE_2024.jpg) |
+-----------------------------------+-----------------------------------------+

Figure 1: The Add Glare Output AOV node used to add a glare effect to a composite node tree

### Add Glare Parameters

Enabled - Determines whether the effect is active or not.

Strength - The amount of glare to apply. 0% means no glare and 100% means the maximum glare possible given the spread start and spread end values. 

Ray Count - Determines the number of glare rays to add. The angle of the rays are evenly spaced around a half circle. 

Angle - The angle of the first glare ray in degrees clockwise from horizontal.

Angle Blur - The width of the range of angles covered by each glare ray in degrees.

Spread Start - The minimum blur radius, as a proportion of image width or height (whichever is larger).

Spread End - The maximum blur radius, as a proportion of image width or height (whichever is larger).

Colorize Strength - The strength with which to apply a rainbow-style color effect to the glare. 

Colorize Phase - Controls the hue of the colorize effect.
