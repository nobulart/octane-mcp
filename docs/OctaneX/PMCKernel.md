The PMC kernel is a custom mutating, unbiased kernel designed for [GPU](javascript:void(0);) rendering. Rendering with PMC creates physically accurate lighting and caustic effects to produce the highest quality results, but it can also take the most time to render, depending on the scene.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_437.png)       | PMC Kernel                                |
|                                   |                                           |
|                                   | ![](images/PMC_Kernel_Fig01_SE_v2022.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The PMC settings in the Node Inspector

 

### PMC Kernel Parameters

 

#### Quality

Max Samples - Sets the maximum number of samples per pixel before the rendering process stops. Higher values produce cleaner renders. There is no rule as to how many samples per pixel are required for a good render - it depends on the content and complexity of the scene.

[Diffuse](javascript:void(0);) Depth - The maximum number of times a ray can bounce, reflect, or refract off of a diffuse or very rough surface. Higher values mean higher render times, but more realistic results. For outdoor renders, a good setting is around 4. For lighting interiors with natural light like the sun and the sky, you need higher values such as 8 or more. In the real world, the maximum diffuse bounces would not exceed 16 - it is possible to use a value higher than 16, but this is not necessary.

[Specular](javascript:void(0);) Depth - Controls the number of times a ray refracts before dying. Higher values mean higher render times, but more color bleeding and more details in transparent materials. Low values introduce artifacts or turn some refractions into pure black.

Scatter Depth - The maximum path depth allowed for scattering.

Maximal Overlapping Volumes - Determines how much space to allocate for overlapping volumes. Ray marching is faster with lo values but it can cause artifacts where many volumes intersect.

Ray Epsilon - The distance between the geometry and the light ray when calculating ray intersections for lighting and shadowing. Larger values push rays away from the geometry surface. Lower values are more accurate, but can cause artifacts on large or distant objects. Ray Epsilon is similar to ray tracing bias in other rendering engines. Adjust Ray Epsilon to reduce artifacts in large-scale scenes.

Filter Size - Sets the filter size in terms of pixels. This can improve aliasing artifacts in the render. However, if the filter is set too high, the image becomes blurry.

Alpha Shadows - Allows any object with transparency (Specular materials, materials with Opacity settings and Alpha Channels) to cast a shadow instead of behaving as a solid object.

Caustic Blur - Reduces noise in caustic light patterns. High values result is softness in the caustic patterns (Figure 2).

GI Clamp - Clamps the contribution for each path to the specified value. By reducing the GI Clamp value, you reduce the amount of fireflies caused by sparse but very strong contributing paths. Reducing this value reduces noise by removing energy.

Nested Dielectrics - If disabled, the surface IORs are not tracked and surface priorities are ignored.

Irradiance Mode - This renders the first surface as a white [Diffuse material](javascript:void(0);). Irradiance Mode works similar to Clay Mode, but it applies to just the first bounce. It disables the Bump channel and makes samples that are blocked by backfaces transparent.

Max Subdivision Level - The maximum subdivision level that should be applied on the geometry in the scene. Setting to 0 disables subdivision.

#### [Alpha Channel](javascript:void(0);)

Alpha Channel - This option removes background images or colors created by the SunSky environment node from the rendered image, while any lighting cast by the environment is unaffected. This is useful if you want to composite the render over another image without having the background present. Objects appearing in the RGB channels have a bleeding edge, which appears as noise artifacts. However, these edges are not included in the Alpha Channel itself.

Keep Environment - Used in conjunction with the Alpha Channel setting. It makes the background visible in the rendered image while keeping the Alpha Channel.

#### Light

- - AI Lights - For more information about the AI Light algorithm and its attributes, see the [AI Light](AILight.md) topic in this manual.
  - Light IDs - For more information about the Light IDs and their attributes, see the [Light Linking And Light Exclusion](LightLinkingandLightExclusion.md) topic in this manual.

#### Sampling

Path Termination Power - This parameter provides a system to tweak samples per second vs. convergence (how fast noise vanishes). Increasing this value causes the kernels to keep paths shorter and spend less time on dark areas, which means they stay noisy longer, but it increases the samples per second. Reducing this value causes kernels to trace longer paths on average and spend more time on dark areas. In short, high values increases the render speed, but may create more noise in dark areas.

Direct Light Rays - Specifies the number of direct light rays traced for every sample. This amount is used after camera rays, and after very smooth specular reflections or transmission.

Exploration Strength - Specifies how long the kernel investigates good paths before it tries to find a new path. Low values create a noisy image, while higher values create a splotchy image.

Direct Light Importance - Causes the kernel to prioritize ray tracing paths with indirect light. Imagine sunlight coming through a window to create a bright spot on the floor. When Direct Light Importance has a value of 1, the kernel samples this area more and reduces noise around the bright spot. If you reduce the Direct Light Importance value, the PMC kernel reduces its efforts to sample that bright area and focuses on more problematic areas that are harder to render, such as areas with more indirect lighting.

Max Rejects - Controls the render bias. Reducing this value results in more bias, but shorter render times. In rendering terminology, biased renders introduce slight blurring and other less accurate computational techniques in order to reduce render time.

Parallel Samples - Controls how many samples are calculated in parallel. Smaller values require less memory to store the sample\'s state, but increases render time. High values require more memory, but reduces render time. The change in performance depends on the scene and the GPU architecture.

Work Chunk Size - The number of work blocks (512K samples each) done per kernel run. Increasing this value increases the memory requirement on the system, but does not affect memory usage, and may increase render speed.

#### Color

White Light Spectrum - Controls the appearance of colors produced by spectral emitters (daylight, environment, black body).This determines the spectrum that will produce white (before white balance) in the final image.

- D65 - Adapts to a reasonable daylight \"white\" color.
- Legacy/Flat - Preserves the appearance of old projects (spectral emitters will appear more blue)

#### Toon Shading

Toon Shadow Ambient - This is the ambient modifier of Toon Shadowing.
