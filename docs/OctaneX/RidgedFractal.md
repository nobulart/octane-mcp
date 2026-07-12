The Ridged Fractal node produces a fractal pattern in grayscale format. In Figure 1, the Ridged Fractal node connects to a [Diffuse material](javascript:void(0);)\'s [Diffuse](javascript:void(0);) pin. Note that the UVW transform scale values (S.X, S.Y, S.Z) are lowered a lot for the pattern to emerge on the surface.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_187.png)       | Ridged Fractal                                  |
|                                   |                                                 |
|                                   | ![](images/Ridged_Fractal_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: A Ridged Fractal texture is connected to a Diffuse material

 

### Ridged Fractal Parameters

Power - Controls the texture\'s overall brightness.

Ridge Height - This specifies the height of the elevated parts of the fractal pattern.

![](images/RidgedFractal_fig2_SEv4_881x443.jpg)

Figure 2: Ridge Height examples

 

Octaves - Controls the amount of detail in the texture.

Omega - This specifies the difference per interval.

![](images/RidgedFractal_fig3_SEv4.jpg)

Figure 3: Omega setting examples

 

Lacunarity - Controls the size of the gaps in the fractal pattern.

UVW Transform - Controls the texture\'s position, scale, and rotation on the surface.

Projection - Determines how the texture projects onto the surface.
