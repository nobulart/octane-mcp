Octane can now leverage RTX hardware acceleration to evaluate previously CUDA-only shaders, such as the new dirt shader. After removing this limitation we have experienced significant 1.6x+ performance increases in many production scenes that previously had almost no speed improvements with RTX activated.

OctaneRender® requires an NVIDIA® CUDA®-enabled video card. It runs on Ada Lovelace, Ampere, Kepler, Maxwell, Pascal, Titan, Volta, and Turing GPUs. Texture limits and differing power efficiency ratings also apply, depending on the GPU microarchitecture. GPUs from the GeForce® line are clocked higher and render faster than the more expensive Quadro® and Tesla GPUs.

GeForce cards are fast and cost-effective, but have less VRAM than Quadro and Tesla cards. OctaneRender scales well in a multi-GPU configuration, and can use different types of NVIDIA cards at once, such as a GeForce RTX 4x or 3x combined with a Quadro 6000. The official list of NVIDIA CUDA-enabled products is located at <https://developer.nvidia.com/cuda-gpus>.

OctaneRender does not require RTX, but it does render some scenes much faster when RT Core hardware is present.

To use the engine\'s out-of-core features, we recommend using at least the following hardware:

- - 8-core CPU, Apple Silicon chip if running on Mac OS
  - 16 GB RAM
  - A CUDA-enabled card with at least 2 GB VRAM

### Looking To Buy A New GPU For OctaneRender®?

There are several things to consider when purchasing a new GPU. You'll want to purchase a video card with the largest amount of VRAM and the most CUDA cores for your budget. Make sure your power supply can handle the new card as well. If you're using a Mac®, make sure that you purchase an Apple®-approved GPU.

To use the OctaneRender denoiser features, you need additional memory to collect all necessary information. As an example, a 4k render requires around 5 GB, while an 8k render requires around 20 GB. High-definition renders require around 0.5 GB.

Memory is also required for geometry, textures, post-processing buffers, and for other 3D modeling software, so it\'s necessary to increase the system RAM along with about 450 MB VRAM on devices to run the denosier. Use out-of-core features to move geometry and textures onto system memory to free up some space for the denoiser on the device.
