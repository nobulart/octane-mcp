The Beauty AOVs are split into two categories, Beauty - Surfaces and Beauty - Volumes. 

#### Beauty - Surfaces

These AOVs are RGB passes of various surface shading attributes.

Denoise Albedo AOV - Outputs the denoised albedo information. 

Denoise Normal AOV - Outputs the denoised scene normal information.

Diffuse AOV -  Outputs only the diffuse component of the scene.

Diffuse Direct AOV - Outputs only the single bounce direct of the scene. No indirect contribution.

Diffuse Filter (Beauty) AOV - Outputs only the non-shaded view of the scene, which are flat regions of the base color or albedo of each material.

Diffuse Indirect AOV - Outputs only indirectly-shaded diffuse pixels within the scene.

Emitters AOV - Outputs any light source or light-contributing pixels of the scene. 

Environment AOV - Outputs any visible portion of the environment in the scene.

Reflection AOV - Outputs only those pixels that receive reflections in the scene.

Reflection Direct AOV - Outputs only those pixels that are directly reflecting light. No bounce reflections are included in this AOV.

Reflection Filter (Beauty) AOV - Outputs only those pixels that are receiving reflections in the scene. Output is grayscale. (check this)

Reflection Indirect AOV - Outputs only those pixels receiving indirect reflections.

Refraction AOV - Outputs any pixels receiving refractions in the scene.

Refraction Filter (Beauty) AOV - Outputs only the unshaded pixels receiving refractions in the scene.

Subsurface Scattering AOV - Outputs only the pixels illuminated by sub-surface scattering.

Transmission AOV - Outputs only those pixels that are transmitting light.

Transmission Filter (Beauty) AOV -  Outputs only unshaded pixels transmitting light in the scene.

#### Beauty - Volumes

These are AOVS that pertain to volume information and shading.

Volume AOV - The volume AOV contains all samples that are scattered in a volume.

Volume Emission AOV - The volume emission AOV contains all of the samples where the camera ray hit a volume emitter.

Volume Mask AOV - The volume mask AOV contains absorption color and the contribution amount of a volume sample. This is a multiplication AOV. To composite volume AOVs, a typical formula would be: (allOtherBeautyPasses)\*volume mask + volume + volume emission.

Volume Z-Depth Back AOV - The volume z-depth back AOV contains the back depth of all volume samples.

Volume Z-Depth Front AOV - The volume z-depth front AOV contains the front depth of all volume samples.
