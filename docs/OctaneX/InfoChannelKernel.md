The Info Channel kernel creates false-color images of the scene containing various types of information about the scene. In scenes where the environment is visible, you should enable the [Alpha Channel](javascript:void(0);).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_433.png)       | Info Channel Kernel                                |
|                                   |                                                    |
|                                   | ![](images/Info_Channel_Kernel_Fig01_SE_v2022.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: The Info Channel parameters

 

### Info Channel Kernel Parameters

 

#### Quality

Max Samples - This sets the maximum number of samples per pixel before the rendering process stops. Higher values result in cleaner renders. There is no rule as to how many samples per pixel are required for a good render - it depends on the content and complexity of the scene being rendered.

Type - This parameter specifies the various passes that the compositing process can render and use.

- Geometric Normals - The vectors perpendicular to the mesh\'s triangle faces.
- Smooth Normals - Shows information on the integrity of the model\'s geometry in terms of the normals perpendicular to the mesh\'s smooth underlying surface.
- Shading Normals - The interpolated normals used for shading. This does not take into account the object\'s Bump map. The result is less faceted and smoother than Geometric Normals.
- Tangent (Local) Normals - A color shows the Tangent (Local) Normal in tangent space at the position hit by the camera ray.
- Z-depth - An image that\'s shaded based on the distance between the objects in the scene and the position of the rendering camera.
- Position - A color-coded image that shows the position of the objects in the scene, often used in compositing to help position 3D-rendered images from different renders.
- Texture Coordinates - A color-coded image showing a Gradient map based on the direction of the object's UV texture coordinates.
- Texture Tangent - The first tangent vector. This determines the Normal map distortion\'s orientation.
- Motion Vector - This renders the 2D motion vector in screen space. The X-coordinate shows pixels set in motion to the right (stored in the Red channel), while the Y-coordinate shows pixels in the up motion (stored in the Green channel).
- [Material](javascript:void(0);) ID - Every material assigned in the scene is represented as a separate color.
- Object Layer ID - A color-coded image, each object is colored based on their Object Layer ID settings. The Layer ID setting is found in the Octane Attributes section in the object's Shape node tab.
- Object Layer Color - Shows the color specified in the Object Layer node.
- Baking Group ID - Every Baking Group ID assigned in the scene is represented as a separate color.
- Light Pass ID - Every Light Pass ID assigned in the scene is represented as a separate color.
- Render Layer ID - A color-coded image, each object is colored based on their Object Layer ID settings. The Layer ID setting is found in the Octane Attributes section in the object's Shape node tab. For more information, see the [Render Layers](javascript:void(0);) topic in this manual.
- Render Layer Mask - A mask that\'s rendered based on an object's Layer ID and render layer membership. For more information, see the Render Layers topic in this manual.
- Wireframe - Triangles outlined in black represent the mesh.
- Ambient Occlusion (AO) - A render that\'s shaded using ambient occlusion calculations. Recessed areas of the surfaces are shaded darker than their surroundings.
- Opacity - An Opacity render mask that\'s based on the object\'s Opacity map.
- Roughness - Based on the material roughness at the camera ray\'s hit point.
- Index Of Refraction (IOR) - Based on the material Index Of Refraction at the camera ray\'s hit point.
- [Diffuse](javascript:void(0);) Filter - Shows the diffuse texture color of the scene\'s Diffuse and [Glossy](javascript:void(0);) materials.
- Reflection Filter - Shows the reflection texture color of the scene\'s [Specular](javascript:void(0);) and Glossy materials.
- Refraction Filter - Shows the refraction texture color of the scene\'s Specular materials.
- [Transmission](javascript:void(0);) Filter - Shows the transmission texture color of the scene\'s Diffuse materials.

Ray Epsilon - The distance between the geometry and the light ray when calculating ray intersections for lighting and shadowing. Larger values push rays away from the geometry surface. Lower values are more accurate, but can cause artifacts on large or distant objects. Ray Epsilon is similar to ray tracing bias in other rendering engines. Adjust Ray Epsilon to reduce artifacts in large-scale scenes.

Filter Size - Sets the filter size in terms of pixels. This can improve aliasing artifacts in the render. However, if the filter is set too high, the image becomes blurry.

AO distance - Sets the maximum distance of the ambient occlusion shading\'s spread.

AO Alpha Shadows - Takes the surface opacity as determined by its shader into account when rendering with the Ambient Occlusion info channel.

Opacity Threshold - While checking Opacity channels, the geometry with an Opacity value greater than or equal to this parameter\'s value is treated as opaque.

Maximum [Z-Depth](javascript:void(0);) - Determines the maximum depth as shown in the shading of the Z-Depth info channel pass.

UV Max - Sets the maximum value shown for the texture coordinates.

UV Coordinate Selection - Specifies the set of UV coordinates to use.

Max Speed - Speed mapped to the maximum intensity in the motion vector channel. A value of 1 specifies a maximum movement of 1 screen width in the shutter interval.

Sampling Mode - Enables motion blur and [depth of field](javascript:void(0);), and sets the pixel filtering modes.

- Distributed Rays - Enables motion blur and [DOF](javascript:void(0);), and enables pixel filtering.
- Non-Distributed with Pixel Filtering - Disabled motion blur and DOF, but leaves pixel filtering enabled.
- Non-Distributed without Pixel Filtering - Disables motion blur and DOF, and disables pixel filtering for all render AOVs except for render layer mask and ambient occlusion.

Bump And Normal Mapping - Enables Bump and Normal map rendering in images created with Info Channel renders.

Wireframe Backface Highlighting - Enables backface highlighting in the Wireframe channel.

Max Subdivision Level - The maximum subdivision level applied on the scene\'s geometry. A value of 0 disables subdivision.

#### Alpha Channel

Alpha Channel - Enables direct lighting through Opacity maps. If disabled, ray tracing is faster, but it renders incorrect shadows for alpha-mapped geometry or Specular materials with Fake Shadows enabled.

#### Sampling

Static Noise - If enabled, the noise patterns are kept stable between frames. 

Parallel Samples - Controls how many samples are calculated in parallel. Small values require less memory to store the sample\'s state, but increases render time. High values require more memory, but reduce render time. The change in performance depends on the scene, the [GPU](javascript:void(0);) architecture, and the number of shader processors contained on the GPU.

Maximum Tile Samples - This controls the number of samples per pixel that OctaneRender® will render until it takes the result and stores it in the frame buffer. A higher value means that results arrive less often in the frame buffer, but reduces the CPU overhead during rendering.

Minimize Net Traffic - If enabled, OctaneRender® distributes the same tile to the net render slaves until it reaches the max samples/pixel, and then it distributes the next tile to slaves. This option doesn\'t affect work done by local GPUs. A Render Node can merge all of its results into the same cached tile until the Primary Render Node switches to a different tile. You should set the maximum samples per pixel to a reasonable value, or else the network rendering focuses on the first tile for a long time.

#### Color

White Light Spectrum - Controls the appearance of colors produced by spectral emitters (daylight, environment, black body).This determines the spectrum that will produce white (before white balance) in the final image.

- D65 - Adapts to a reasonable daylight \"white\" color.
- Legacy/Flat - Preserves the appearance of old projects (spectral emitters will appear more blue)

[](javascript:void(0);)

#### [Deep Image](javascript:void(0);)

Deep Image - Enables deep pixel image rendering for deep image compositing. It is covered in more detail in the [Deep Image Rendering](DeepImageRendering.md) topic in this manual.

Deep [Render Passes](javascript:void(0);) - Includes render passes for deep image pixels.

Maximum Depth Samples - This is used when Deep Image Rendering is enabled. It sets the maximum number of depth samples per pixel, and is covered in more detail in the Deep Image Rendering topic in this manual.

Depth Tolerance - This is used when Deep Image Rendering is enabled. The depth samples with a relative depth difference below this value are merged together. This is covered in more detail in the Deep Image Rendering topic in this manual.
