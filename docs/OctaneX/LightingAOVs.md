The Light AOVs isolates a light source\'s contribution. Each light AOV behaves as if all the other lights in the scene are switched off. You can combine individual light AOVs to recreate the original render in post, or to further adjust the individual contributions of each light during post. There are three light AOVs avaiable in Octane.

- Light AOV - A generic light AOV (defaults to sunlight). Choose the desired Light ID from the ID drop down menu.
- Light Direct AOV - Outputs only the direct light contribution of the specified Light ID.
- Light Indirect AOV - Outputs only the indirect light contribution of the specified Light ID.

To use light AOVs, each light emitter needs to be identified and mapped to the desired Light AOV. This is done by assigning the Light Pass ID in each Emission node in the scene (figure 1).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_479.png)       | Light Pass ID                               |
|                                   |                                             |
|                                   | ![](images/Lighting_AOVs_Fig01_SE_2023.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 1: Assign Light pass ID in the Emission nodes

A Light AOV node with a corresponding Light ID needs to be added to the Render AOV Group node (figure 2).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_480.png)       | Light Pass ID                               |
|                                   |                                             |
|                                   | ![](images/Lighting_AOVs_Fig02_SE_2023.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 2: Setting the Light AOV node\'s ID to coorespond with the appropriate light source

To see the AOV, enable the lighting AOVs according to the existing assigned IDs in the Render Viewport (figure 3).

+-----------------------------------+---------------------------------------------+
| ![](images/NewItem_481.png)       | Light AOV Render Viewport                   |
|                                   |                                             |
|                                   | ![](images/Lighting_AOVs_Fig03_SE_2023.jpg) |
+-----------------------------------+---------------------------------------------+

Figure 3: Enabling the light AOV in the render viewport
