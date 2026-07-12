The AOV Collections category provides nodes that combine common types of AOVs together into one node, eliminating the need to add each AOV node separately (figure 1). Many of the AOV Collection nodes have an option between simple which provides the most commonly used AOVs and detailed which provides access to all the associated AOV type. 

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_575.png)       | AOV Collections                               |
|                                   |                                               |
|                                   | ![](images/AOV_Collections_Fig01_SE_2024.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: The Beauty AOVs (Simple) node connected to the Render AOVs pin on a Render Target node

### Common AOV Collections Parameters

Enabled - Determines whether the node is active or not. 

Raw - Converts the AOVs to raw AOVs by factoring out the color of the BxDF of the surface hit by the camera ray. 

Cyptomatte Bins - The number of Cryptomatte bins to render.

Max Info Samples - The maximum number of samples for the info passes.

Info Sampling Mode - Enables motion blur and depth of field, and sets the pixel filtering modes.

- Distributed Rays - Enables motion blur and DOF, and also enables pixel filtering. 
- Non-Distributed with Pixel Filtering - Disables motion blur and DOF, but leaves pixel filtering enabled. 
- Non-Distributed without Pixel Filtering - Disables motion blur and DOF, and disables pixel filtering for all render AOVs except for render layer mask and ambient occlusion.

Info Opacity Threshold - Geometry with an opacity higher or equal to this value is treated as completely opaque. 

AOVs - The list of available AOVs. The Add Render AOV button can be used to add more AOV slots.
