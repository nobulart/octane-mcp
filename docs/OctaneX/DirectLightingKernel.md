The Direct Light kernel is used for faster preview rendering. Direct Lighting is not unbiased and will not yield photorealistic results, but because of its speed, it is ideal for rendering animations or stills, depending on the project\'s demands.

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_430.png)       | Direct Lighting KErnel                                 |
|                                   |                                                        |
|                                   | ![](images/Direct_Lighting_Kernel_Fig01_SE_v_2023.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 1: The Direct Lighting settings in the Node Inspector

 

### Direct Lighting Kernel Parameters

 

#### Quality

Max. Samples - Sets the maximum number of samples per pixel before the rendering process stops. Higher values result in cleaner renders. There is no rule as to how many samples per pixel are required for a good render - it depends on the content and complexity of the scene being rendered.

Global Illumination Mode - There are three types of Global Illumination modes in the Direct Lighting kernel:

- None - Includes direct lighting from the sun or area lights. Shadowed areas receive no contribution, and will be black.
- Ambient Occlusion - Standard ambient occlusion. This mode provides realistic images, but offers no color bleeding.
- [Diffuse](javascript:void(0);) - This gives a GI quality that is in between Ambient Occlusion and Path Tracing, but without caustics. The advantage is much faster rendering than Path Tracing and PMC. It is similar in some ways to brute force indirect GI in other engines.

[Specular](javascript:void(0);) Depth - Controls the number of times a ray refracts before dying. Higher numbers mean higher render times, but more color bleeding and more details in transparent materials. Low numbers introduce artifacts or turn some refractions into pure black. Examples of various Specular Depths using the Direct Lighting kernel with GI Mode set to None are shown in Figure 2.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_431.png)       | Specular Depth                            |
|                                   |                                           |
|                                   | ![](images/DirectLightingKernelFig_3.png) |
+-----------------------------------+-------------------------------------------+

Figure 2: A comparison of renderings using different Specular Depth settings

[Glossy](javascript:void(0);) Depth - Controls the number of times a ray reflects before dying. Higher numbers mean higher render times. Values lower than 4 can introduce artifacts, or turn some reflections into pure black.

Diffuse Depth - Gives the maximum number of diffuse reflections if GI Mode is set to Diffuse.

Maximal Overlapping Volumes - Determines how much space to allocate for overlapping volumes. Ray marching is faster with low values but it can cause artifacts where many volumes intersect.

Ray Epsilon - The distance between the geometry and the light ray when calculating ray intersections for lighting and shadowing. Larger values push rays away from the geometry surface. Lower values are more accurate, but cause artifacts on large or distant objects. Ray Epsilon is similar to ray tracing bias in other rendering engines. Adjust Ray Epsilon to reduce artifacts in large-scale scenes.

Filter Size - Sets the filter size in terms of pixels. This improves aliasing artifacts in the render. However, if the filter is set too high, the image can become blurry.

AO Distance - The distance of the ambient occlusion shadowing spread in units. This setting provides realistic results, depending on the scale of the objects in the scene. Small values are more appropriate for small objects like toys, and larger values are more appropriate for something like a house (Figure 3).

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_432.png)       | AO Distance                       |
|                                   |                                   |
|                                   | ![](images/AOdistance_133.png)    |
+-----------------------------------+-----------------------------------+

Figure 3: AO Distance settings comparison

AO Ambient Texture - Specifies an Ambient Occlusion texture, which is used for the AO calculation instead of the environment. If AO Ambient Texture is disabled, the environment is used instead. This gets rid of the blue tint on white walls caused by the blue sky (like Octane Day Light).

Alpha Shadows - This enables direct light through Opacity maps. If disabled, ray tracing is faster, but it renders incorrect shadows for alpha-mapped geometry or Specular materials with fake shadows enabled. Alpha Shadows allows any object with transparency (Specular materials, materials with Opacity settings, and Alpha Channels) to cast a shadow instead of behaving as a solid object.

Nested Dielectrics - If disabled, the surface IORs are not tracked and surface priorities are ignored.

Irradiance Mode - This renders the first surface as a white Diffuse material. Irradiance Mode is similar to Clay Mode, but it applies to just the first bounce. It disables the Bump channel and makes samples that are blocked by back faces transparent.

Max Subdivision Level - The maximum subdivision level that should be applied on the geometry in the scene. A value of 0 disables subdivision.

#### [Alpha Channel](javascript:void(0);)

Alpha Channel - Removes background images or colors created by the SunSky environment node from the rendered image while not affecting any lighting cast by the environment. This is useful if the you want to composite the render over another image without the background being present. Objects appearing in the RGB channels have a bleeding edge, which appear as noise artifacts, but these edges are not included in the Alpha Channel itself.

Keep Environment - Used in conjunction with the Alpha Channel setting. It makes the background visible in the rendered image while also keeping the Alpha Channel.

#### Light

AI Lights - For more information about the AI Light algorithm and its attributes, see the [AI Light](AILight.md) topic in this manual.

Light IDs - For more information about the Light IDs and their attributes, see the [Light Linking And Light Exclusion](LightLinkingandLightExclusion.md) topic in this manual.

#### Sampling

Path Termination Power - Provides a system to tweak samples per second vs. convergence (how fast noise vanishes). Higher values cause the kernels to keep paths shorter and spend less time on dark areas, which means they stay noisy longer, but it increases the samples per second. Lower values cause kernels to trace longer paths on average and spend more time on dark areas. In short, high values increases the render speed, but lead to more noise in dark areas.

Direct Light Rays - Specifies the number of direct light rays traced for every sample. This amount is used after camera rays, and after very smooth specular reflections or transmission. 

Coherent Ratio - Increasing this value increases the render speed, but it introduces low-frequency noise or blotches. Eliminating the blotchy appearance requires a few hundred or even a few thousand samples per pixel, depending on the scene\'s contents.

Static Noise - Keeps noise patterns static between rendered frames in a sequence. The noise is static as long as the same [GPU](javascript:void(0);) architecture is used for rendering. Different architectures produce different numerical errors, which manifest as small differences in the noise pattern.

Parallel Samples - Controls how many samples OctaneRender® calculates in parallel. Smaller values require less memory to store the sample\'s state, but causes slower renders. High values require more memory, but reduce the render time. The change in performance depends on the scene and the GPU architecture.

Maximum Tile Samples - Controls the number of samples per pixel that OctaneRender® will render before storing the result in the render buffer. Higher values mean that results arrive less often in the film buffer.

Minimize Net Traffic - Distributes the same tile to the net render nodes until OctaneRender® reaches the maximum number of samples per pixel for that tile, and then it distributes the next tile to Render Nodes. This option doesn\'t affect work done by local GPUs. A Render Node can merge all of its results into the same cached tile until the Primary Render Node switches to a different tile.

[](javascript:void(0);)

#### [Adaptive Sampling](javascript:void(0);)

Adaptive Sampling - This section provides options to use the Adaptive Sampling capabilities of OctaneRender, especially in scenes with complex lighting. For more information, see the [Adaptive Sampling](AdaptiveSampling.md) topic in this manual.

#### Color

White Light Spectrum - Controls the appearance of colors produced by spectral emitters (daylight, environment, black body).This determines the spectrum that will produce white (before white balance) in the final image.

- - D65 - Adapts to a reasonable daylight \"white\" color.
  - Legacy/Flat - Preserves the appearance of old projects (spectral emitters will appear more blue)

[](javascript:void(0);)

#### [Deep Image](javascript:void(0);)

Deep Image - Enables deep pixel image rendering for deep image compositing. For more information, see the [Deep Image Rendering](DeepImageRendering.md) topic of this manual.

Deep [Render Passes](javascript:void(0);) - Includes render passes for deep image pixels.

Maximum Depth Samples - Used when Deep Image Rendering is enabled. It sets the maximum number of depth samples per pixel. For more details, read the Deep Image Rendering topic in this manual.

Depth Tolerance - Used when Deep Image Rendering is enabled. OctaneRender merges depth samples whose relative depth difference falls below this tolerance value. For more information, see the Deep Image Rendering topic in this manual.

#### Toon Shading

Toon Shadow Ambient - This is the ambient modifier of Toon Shadowing.
