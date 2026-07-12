The Fractal Flow Noise procedural texture produces a 3D noise pattern comprised of two color parameters (figure 1).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_171.png)       | Fractal Flow Noise                                 |
|                                   |                                                    |
|                                   | ![](images/Fractal_Flow_Noise_Fig01_SE_v_2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: The Fractal Flow Noise texture applied to a [Diffuse material](javascript:void(0);) on a plane primitive

 

### Fractal Flow Noise Parameters

Colors 1 and 2 - Specifies the two colors used for the flow noise.

Flow - Controls the position of the noise pattern, capable of producing an animated effect.

Lacunarity - Specifies the size of the gaps within the noise pattern.

Flow Rate - A multiplier per iteration for the flow coordinate.

Gain - Amplitude multiplier per iteration, provides an overall contrast control for the noise pattern.

Advection - Provides both an initial advections amount and an advection multiplier per iteration, where higher values will smooth the noise results.

Octaves - Changes the number of octaves over which the noise function is calculated, otherwise known as frequencies.

Attentuation - The power of the falloff applied to the final result, providing an overall lightening or darkening of the noise pattern.

Step Noise - Provides a smooth noise result when disables, and a stepped noise result with enabled.

UVW Transform - Positions, scales, and rotates the surface texture.

Projection - Sets how the texture projects onto the surface.
