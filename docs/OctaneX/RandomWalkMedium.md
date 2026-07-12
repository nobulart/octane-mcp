The Random Walk node is a newer variant of subsurface scattering that utilizes a stochastic or random process for the scattering of light through an object. This provides the most realistic result when rendering scatter volumes. The Random Walk parameters are similar to the [Scattering](javascript:void(0);) node\'s parameters with a few exceptions (Figure 1).

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_127.png)       | Random Walk Parameters                     |
|                                   |                                            |
|                                   | ![](images/Random_Walk_Fig01_SE_v2024.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 1: The Random Walk parameters.

 

### Random Walk Parameters

Density - Determines the density of the particles in the surface. The larger the scale value, the more likely light will be absorbed when passing through the surface.

Volume Step % - Depending on the surface, you may need to adjust this parameter as it is specified as a percentage of the voxel size. The default value is 100%, but if the volume is smaller than this, you need to decrease the value. Decreasing this value decreases render speed, and increasing the value causes the ray marching algorithm to take longer steps. If the Volume Step % exceeds the volume\'s dimensions, then the ray marching algorithm takes a single step through the whole volume. To get the most accurate results, keep Volume Step % as small as possible.

Volume Shadow Ray Step % - Step length that is used by the shadow ray for marching through volumes.

Use Volume Step Length for Volume Shadow Ray Step Length - If active, uses Volume Step Length as Volume Shadow Ray Step as well.

Sample Position [Displacement](javascript:void(0);) - Allows a texture to control a volume\'s sample position displacement.

Volume Padding - Expands the volume bounding box by the given percentage in all six directions, but only if sample position displacement is being used. 

Albedo - Determines the color that is being scattered.

Radius - Determines the depth that the light scatters in the medium where black provides no scattering and white fully scatters. A color node or a float value can be used with this attribute as well. A color node\'s Value amount plays an important roll with this attribute. A darker value will scatter this color less and a lighter value will scatter this color more.

Bias - The bias of the subsurface scattering. Higher values use biased sampling, which usually yields better results with lower depth settings. Visually, lower values will bias towards the Radius color and higher values will bias towards the Albedo color.
