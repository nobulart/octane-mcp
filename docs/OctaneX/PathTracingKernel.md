The Path Tracing kernel is a better choice for rendering photorealistic images than the Direct Lighting kernel. The increase in quality comes with the cost of increased render times. Path Tracing may have difficulty rendering scenes that use small light sources, and may not render proper caustics well. In these situations, the PMC render kernel is the better choice. Testing renders using each of the render kernels is the best way to determine what kernel is the best choice for a given scene.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_435.png)       | Path Tracing                               |
|                                   |                                            |
|                                   | ![](images/Path_Tracing_Fig01_SE_2023.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 1: Path Tracing settings in the Node Inspector

 

### Path Tracing Parameters

#### Quality

Max. Samples - Sets the maximum number of samples per pixel before the rendering process stops. Higher values result in cleaner renders. There is no rule as to how many samples per pixel are required for a good render - it depends on the scene\'s content and complexity.

[Diffuse](javascript:void(0);) Depth - The maximum number of times a ray can bounce off of a diffuse or very rough surface. Higher values mean higher render times, but more realistic results. For outdoor renders, a good setting is around 4. For lighting interiors with natural light from the sun and sky, you need settings of 8 or higher. In the real world, the maximum diffuse bounces would not exceed 16. It is possible to use a value higher than 16, but this is not necessary.

[Specular](javascript:void(0);) Depth - Controls the number of times a ray refracts before dying. Higher values lead to higher render times, but more color bleeding and more details in transparent materials. Low values introduce artifacts or turn some refractions into pure black.

Scatter Depth - The maximum path depth that allows scattering.

Maximal Overlapping Volumes - Determines how much space to allocate for overlapping volumes. Ray marching is faster with lo values but it can cause artifacts where many volumes intersect.

Ray Epsilon - The distance between the geometry and the light ray when calculating ray intersections for lighting and shadowing. Larger values push rays away from the geometry surface. Smaller values are more accurate, but cause artifacts on large or distant objects. Ray Epsilon is similar to ray tracing bias in other rendering engines. Adjust Ray Epsilon to reduce artifacts in large-scale scenes.

Filter Size - Sets the filter size in terms of pixels. This can improve aliasing artifacts in the render. However, if the filter is set too high, the image becomes blurry.

Alpha Shadow - Allows any object with transparency (Specular materials, materials with Opacity settings and Alpha Channels) to cast a shadow instead of behaving as a solid object.

Caustic Blur - Reduces noise in caustic light patterns. High values result in soft caustic patterns (see Figure 2).

GI Clamp - Clamps the contribution for each path to the specified value. By reducing the GI Clamp value, you can reduce the amount of fireflies caused by sparse but very strong contributing paths. Reducing this value reduces noise by removing energy.

Nested Dielectrics - If disabled, the surface IORs are not tracked and surface priorities are ignored.

Irradiance Mode - This renders the first surface as a white Diffuse material. Irradiance Mode works similar to Clay Mode, but it applies to the first bounce. It disables the Bump channel and makes samples that are blocked by back faces transparent.

Max Subdivision Level - The maximum subdivision level applied on the scene\'s geometry. A value of 0 disables subdivision.

#### [Alpha Channel](javascript:void(0);)

Alpha Channel - This option removes background images or colors created by the SunSky environment node from the rendered image while not affecting any lighting cast by the environment. This is useful if you want to composite the render over another image without the background being present. Objects appearing in the RGB channels have a bleeding edge, which appears as noise artifacts. These edges are not included in the Alpha Channel itself.

Keep Environment - Used in conjunction with the Alpha Channel setting. It makes the background visible in the rendered image while keeping the Alpha Channel.

#### Light

AI Lights - For more information about the AI Light algorithm and its attributes, see the [AI Light](AILight.md) topic in this manual.

Light IDs - For more information about the Light IDs and their attributes, see the [Light Linking And Light Exclusion](LightLinkingandLightExclusion.md) in this manual.

#### Sampling

Path Termination Power - Tweaks samples-per-second vs. convergence (how fast noise vanishes). Increasing this value causes the kernels to keep paths shorter and spend less time on dark areas, which means they stay noisy longer, but it also increases samples-per-second. Reducing this value causes kernels to trace longer paths on average and spend more time on dark areas. In short, high values increase the render speed, but they may lead to higher noise in dark areas.

Direct Light Rays - Specifies the number of direct light rays traced for every sample. This amount is used after camera rays, and after very smooth specular reflections or transmission.

Coherent Ratio - Increasing this value increases the render speed, but it also introduces low-frequency noise or blotches. Eliminating the blotchy appearance requires a few hundred or a few thousand samples per pixel to go away, depending on the contents of the scene. Figure 4 shows a render comparison using different Coherent Ratio settings.

Static Noise - Keeps noise patterns static between rendered frames in a sequence. The noise is static as long as the same [GPU](javascript:void(0);) architecture is used for rendering. Different architectures produce different numerical errors, which manifest as small differences in the noise pattern.

Parallel Samples - Controls how many samples OctaneRender® calculates in parallel. Smaller values require less memory to store the sample\'s state, but increase render time. Larger values require more memory, but reduce render time. The change in performance depends on the scene and the GPU architecture.

Max Tile Samples - Controls the number of samples per pixel that OctaneRender will render before storing the result in the render buffer. Higher values mean that results arrive less often in the film buffer.

Minimize Net Traffic - Distributes the same tile to the net render slaves until OctaneRender reaches the max samples-per-pixel for that tile, and then it distributes the next tile to slaves when enabled. This option doesn\'t affect work done by local GPUs. A Render Node can merge all of its results into the same cached tile until the Primary Render Node switches to a different tile.

#### [Adaptive Sampling](javascript:void(0);)

Adaptive Sampling - This section provides options to use the Adaptive Sampling capabilities of OctaneRender, especially in scenes with complex lighting. For more information, see the [Adaptive Sampling](AdaptiveSampling.md) topic in this manual.

#### Color

White Light Spectrum - Controls the appearance of colors produced by spectral emitters (daylight, environment, black body).This determines the spectrum that will produce white (before white balance) in the final image.

- D65 - Adapts to a reasonable daylight \"white\" color.
- Legacy/Flat - Preserves the appearance of old projects (spectral emitters will appear more blue)

[](javascript:void(0);)

#### [Deep Image](javascript:void(0);)

Deep Image - Enables deep pixel image rendering for deep image compositing. For more information, see the [Deep Image Rendering](DeepImageRendering.md) topic of this manual.

Deep Render AOVs - Includes AOVs for deep image pixels.

Maximum Depth Samples - Used when Deep Image Rendering is enabled. It sets the maximum number of depth samples per pixel. For more details, read the Deep Image Rendering topic in this manual.

Depth Tolerance - Used when Deep Image Rendering is enabled. OctaneRender merges depth samples whose relative depth difference falls below this tolerance value. For more information, see the Deep Image Rendering topic in this manual.

#### Toon Shading

Toon Shadow Ambient - This is the ambient modifier of Toon Shadowing.
