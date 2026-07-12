OctaneRender® is a spectral renderer, so it handles the color variable type in a somewhat non-standard way.

 

#### Spectrum And RGB

Depending on what returned a given color value, a color variable is represented internally as RGB or as a spectral color. When expressions use both RGB colors and spectral colors, the RGB colors are converted to spectral colors.

A is an RGB color:

color a = 1;

B is an RGB color:

color b = {1, 0.5, 0};

C is a spectral color:

color c = \_gaussian(1, 0.5, 0.01);

Adding two RGB colors results in another RGB color:

color d = a + b

+------------------------------------------------------------------------------+
| NOTE:                                                                        |
|                                                                              |
| Adding a spectral color to another color always results in a spectral color. |
+------------------------------------------------------------------------------+

In practice, most colors end up representing as RGB colors. The main exceptions are blackbody and Gaussian spectra.

RGB colors support element access (using \[\]) and casting to point-like types. For spectral colors, this can be done as an approximation, and the result will have poor color fidelity. The compiler will emit a warning if this happens.

To learn more about programming with the [Open Shader Language](javascript:void(0);), see [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).
