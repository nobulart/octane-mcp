Light linking provides a way to include and exclude illumination contributions of light sources on objects in a scene. The light IDs are set in Emitter nodes under the Emission rollout (figure 1), and this light ID corresponds to the Light IDs found in the Kernel Settings (figure 2). OctaneRender® has twenty Light IDs, and you can also choose whether to enable the sun and environment separately.

+-----------------------------------+--------------------------------------------------------------+
| ![](images/NewItem_397.png)       | Light Pass ID                                                |
|                                   |                                                              |
|                                   | ![](images/Light_Linking_Light_Exclusion_Fig01_SE_v2026.jpg) |
+-----------------------------------+--------------------------------------------------------------+

Figure 1: Setting Light Pass IDs in the Emission parameters for an Octane light source

Light linking and light exclusion settings are found under the Light section in the Kernel Settings.

+-----------------------------------+-------------------------------------------------------------+
| ![](images/NewItem_398.png)       | Light ID Kernel Settings                                    |
|                                   |                                                             |
|                                   | ![](images/LightLinkingAndLightExclusion_Fig03_SEv4-00.jpg) |
+-----------------------------------+-------------------------------------------------------------+

Figure 3: Light Linking and Light Exclusion controls are accessed via the Light section of the Kernel settings

 

### Light Linking And Light Exclusion Parameters

Light ID Action - Either enables or disables the specified light IDs in the Light IDs parameter.

Light IDs Determines which light IDs to render.

Light Linking Invert - These are used by the light linking and light exclusion features for Emitter nodes. You can enable or disable Light IDs globally in the Kernel Settings. The Light Linking Invert option inverts the light linking behavior for selected light IDs.
