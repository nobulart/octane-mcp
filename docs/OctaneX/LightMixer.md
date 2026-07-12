The Light Mixer blend node allows for efficient mixing of multiple Light AOV render nodes. This node eliminates the need for individual Render AOV nodes in the compositing node tree for each Light AOV render node (figure 1). Additionally, each light ID in this node has an intensity multiplier and tint setting which provides a post-render option for making tint and intensity edits. 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_540.png)       | Light Mixer                               |
|                                   |                                           |
|                                   | ![](images/Light_Mixer_Fig01_SE_2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Light Mixer node used to blend light IDs 2 and 3 together

### Light Mixer Parameters

Enabled - Determines whether the Light Mixer node is active or not.

Sunlight - Controls the sunlight results in the composite tree if a Daylight Environment is used.

Ambient Light - Controls the ambient light produced by the environment lighting systems. 

Light IDs - Corresponds to the Light AOVs set up in the Render AOV Group node. 

Blending Settings - Determines the blending mode for the entire light group.
