The Standard [Volume Medium](javascript:void(0);) node is a volume medium node with comprehensive controls for adjusting volume, scatter, transparency, emission, and temperature parameters based on imported VBD grid data (figure 1).

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_128.png)       | Standard Volume Medium                                 |
|                                   |                                                        |
|                                   | ![](images/Standard_Volume_Medium_Fig01a_SE_v2022.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 1: The Standard Volume Medium node connected to an imported [VDB](javascript:void(0);) file using the density and temperature grid data to drive the various parameters for volume shading

 

### Standard Volume Medium Parameters

#### Volume

Density - Determines the density of the particles in the volume. Other attributes such as absorption, scattering, and emission will be amplified as this value is increased.

Density Channel - Further specifies density distribution from the imported VBD\'s grid data.This data is typically imported with the VDB file as density, temperature, heat, etc.

Interpolation - Determines the interpolation mode used when reading voxel data from the channel inputs.

Volume Step % - Depending on the surface, you may need to adjust this parameter as it is specified as a percentage of the voxel size. The default value is 100%, but if the volume is smaller than this, you need to decrease the value. Decreasing this value decreases render speed, and increasing the value causes the ray marching algorithm to take longer steps. If the Volume Step % exceeds the volume\'s dimensions, then the ray marching algorithm takes a single step through the whole volume. To get the most accurate results, keep Volume Step % as small as possible.

Volume Shadow Ray Step % - Step length that is used by the shadow ray for marching through volumes.

Use Volume Step Length for Volume Shadow Ray Step Length - Check box for using the Volume Step Length for the Volume Shadow Ray Step Length as well.

Single Scatter Amount - Determines how often direct light is calculated in volumes, as a ratio of scatter events. Larger values will tend to soften the volume especially around the edges.

Sample Position [Displacement](javascript:void(0);) - Allows a texture to control a volume\'s sample position displacement.

Volume Padding - Expands the volume bounding box by the given percentage in all six directions, but only if sample position displacement is being used. 

#### Scatter

Scatter Weight - Specifies the amount of scatter applied to the volume.

Scatter Color - Determines the color of the scatter characteristics.

Scatter Color Channel - Further specifies scatter distribution from the imported VBD\'s grid data.This data is typically imported with the VDB file as density, temperature, heat, etc.

Scatter Anisotropy - Determines the light scattering direction where negative values produce backward scattering and positive values result in forward scattering.

#### Transparency

Transparency Weight - Specifies the amount of transparency applied to the volume.

Transparency Depth - Provides additional control over the transparency density of the volume.

Transparency Channel - Further specifies transparency distribution from the imported VBD\'s grid data.

#### Emission

Emission Mode - Determines the mode to calculate emission. The [Black Body](javascript:void(0);) option additionally uses the Temperature parameters to control emission, otherwise the Temperature parameters have no effect.

Emission Weight - Specifies the amount of emission applied to the volume.

Emission Color - This color\'s value data is a multiplier on the emission weight, the color itself will tint the emission.

Emission Channel - Further specifies emission distribution from the imported VBD\'s grid data.

Light Pass ID - The Light Pass ID captures the respective emitter\'s contribution.

#### Temperature

Temperature - Specifies the amount of temperature applied to the emission when the Emission Mode is set to Black Body.

Temperature Channel - Further specifies temperature distribution from the imported VBD\'s grid data.

Black Body Kelvin - Scales the temperature values specified in the temperature channel using the Kelvin scale where lower values are cooler and higher values are warmer.

Black Body Intensity - Scales the intensity of the black body emission.

Auto Scale Temperature Channel - Adjusts the temperature values so the maximum value in the channel is mapped to the black body temperature specified in Kelvin. Activating this parameter is common in order to scale back the perceived brightness of the emission.
