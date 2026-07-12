Octane\'s AI Denoiser uses Machine Deep Learning to remove sampling noise on images and animation frames. Although there are several denoiser products on the market, the AI Denoiser in Octane is a \"Spectral AI Denoiser\" and produces superior results. The Spectral AI Denoiser lets you render noise-free images with the Path Tracing and Photon Tracing kernels in a short amount of time. The denoiser is not trained for the PMC kernel. The AI Denoiser is also trained to denoise volumes and volume passes. Volumetric passes have very low frequency details, so don\'t use the Volumetric AI Denoiser with less than 1000 samples in order to preserve details for final render quality that would resemble a 2K to 10K sample render of the scene.

The Denoised AOVs are a denoised subset of the Beauty Surfaces and Volumes AOVs

- Denoiser Diffuse Direct AOV - This AOV contains the denoised result of the diffuse direct render pass.
- Denoiser Diffuse Indirect AOV - This AOV contains the denoised result of the diffuse indirect render pass.
- Denoiser Emission AOV - This AOV contains the denoised result of the emission render pass.
- Denoiser Reflection Direct AOV - This AOV contains the denoised result of the reflection direct render pass.
- Denoiser Reflection Indirect AOV - This AOV contains the denoised result of the reflection indirect render pass.
- Denoiser Remainder AOV - This AOV contains the denoised result of the transmission and sub-surface render passes.
- Denoiser Volume AOV - This AOV contains the denoised result of the volume render pass. 
- Denoiser Volume Emission AOV - This AOV contains the denoised result of the volume emission render pass.
