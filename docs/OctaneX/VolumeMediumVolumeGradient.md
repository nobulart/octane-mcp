Volume mediums add color and other qualities to a [VDB](javascript:void(0);) file. VDBs are a generic volume format that create effects such as smoke, fog, vapor, and similar gaseous objects. VDBs are generated and exported from other 3D software programs. You can also download VDB files from www.openvdb.org/download. VDBs can be a single frame, or an animated file sequence. To use a VDB, right-click in the Node Graph Editor and choose on Volume from the Geometry context menu (figure 1). Use the file browser to locate the VDB file on your local drive.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_491.png)       | Volume Node                                   |
|                                   |                                               |
|                                   | ![](images/Volume_Mediums_Fig01_SE_v2023.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 1: Clicking on Volume node

Next, attach a Volume medium to the VDB node, and connect the VDB node to a Render Target. When you select the Render Target, it becomes visible in the Viewport. Y ou may need to zoom out to see it if the volume is very large. Additionally, a Standard [Volume Medium](javascript:void(0);) can be used. See the section on [Mediums](javascript:void(0);) - Subsurface [Scattering](javascript:void(0);) and Volumes for more information.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_492.png)       | Volume Medium Node                |
|                                   |                                   |
|                                   | ![](images/VDBnetwork.png)        |
+-----------------------------------+-----------------------------------+

Figure 2: A Volume medium connected to a VDB file, which is then connected to a Render Target

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_493.png)       | VDB File                                      |
|                                   |                                               |
|                                   | ![](images/Volume_Mediums_Fig03_SE_v2022.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 3: A VDB file rendered in the Octane Viewport

The volume medium has a number of parameters used to edit the look of the volume. Volume Gradients can be added to the [Absorption](javascript:void(0);) Ramp and/or Scattering Ramp pins for more control over the look of the volume. When using volume gradients for the absorption ramp, the Start Value must be white.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_494.png)       | Volume Medium Parameters                      |
|                                   |                                               |
|                                   | ![](images/Volume_Mediums_Fig04_SE_v2022.jpg) |
+-----------------------------------+-----------------------------------------------+

Figure 4: Volume medium parameters in the Node Inspector

 

### The Volume Medium Parameters

Density - This parameter multiplies against Scattering.

Volume Step % - Only applicable when rendering Volume mediums. This attribute may need to be adjusted depending on the surface and it is a percentage of the voxel size . The default value for the step % is 100. For smaller volumes, the step percentage will need to be decreased. Please note that decreasing this will reduce the render speed. Increasing this value will cause the ray marching algorithm to take longer steps. Should the step % far exceed the volume's dimensions, then the ray marching algorithm will take a single step through the whole volume. Most accurate results are obtained when the step % is as small as possible.

Volume Shadow Ray Step % - Step % that is used by the shadow ray for marching through volumes.

Use Volume Step Length for Volume Shadow Ray Step Length - Check box for using the Volume Step Length for the Volume Shadow Ray Step Length as well.

Single Scatter Amount - Determines how often direct light is calculated in the volume.

Sample Position [Displacement](javascript:void(0);) - Allows a texture to control a volume\'s sample positions displacement.

Volume Padding - Expands the volume bounding box by the given percentage in all 6 directions, but only if sample position displacement is being used. 

Absorption - Specifies the absorption color texture.

Absorption Ramp - The Absorption color ramp that defines the color\'s range. The Absorption ramp takes the grid value as input. In the color gradient, the colors near 0 on the left side of the ramp are mapped to the lower values of the volume, which are areas of lower density. Colors on the right side of the gradient are mapped to higher grid values, where the volume density is greater. Emission and Scattering ramps operate in a similar way.

When using Ramps to shade an animated VDB sequence, pay attention to the Ramp\'s Max, which normalizes the Volume grid values by keeping them between 0 and 1 so the Ramp colors can map to the Volume grid. The grids\' maximum values are sometimes very different throughout VDB sequences from one frame to the next. If you set a Max value too high or too low, you will see just a subset of the colors in the specified gradient.

Invert Absorption - Inverts the Absorption color so that the Absorption channel becomes a Transparency channel. This helps visualize the effect of the specified color since a neutral background shining through the medium appears close to that color.

Scattering - The scattering cross section. This channel defines how much light is absorbed over the color range.

Scattering Ramp - Acts similar to the Absorption ramp, but instead it maps colors to the light as it scatters within the volume.

Phase - Determines the scattering direction. Negative values mean backwards scattering, 0 means equal scattering in all directions, and positive values mean forward scattering.

Emission - This sets the Volume emission to accept volumetric emission modes. For emission, the Medium node can have either a Blackbody Emission node or a Texture Emission node.

When using the Blackbody Emission node, make sure that the emission grid data contains temperatures in Kelvin. VDBs often have unit-less temperatures with arbitrary ranges such as 0 - 1 or 0 - 45, as is the case with some sample VDBs from openvdb.org. Typical temperature values range between 0 - 6500, where lower values create longer wavelengths, and higher values create shorter wavelengths. In order to get realistic results from the Blackbody Emission for volumes, disable Normalize in the Emission node. Lower temperatures give off less light than higher temperatures, but when normalized, the radiance emitted by all temperatures is equal.

When using the Texture Emission node, the input temperature grid is interpreted as emission power, not emission temperature. This is more linear in that the higher the temperature value, the more light it gives off at that point. Once volume gradients are implemented, you can control the color more precisely.

Emission Ramp - The Emission color ramp.

Make sure the volume is not too dense. We recommend reducing the Volume Step Length to an acceptable performance and accuracy level, and then reduce the Volume Density. Otherwise you may risk rendering a solid object at a high step length.
