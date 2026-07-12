List Of Intrinsic Functions - Using intrinsics defined by OctaneRender® requires including \<octane-oslintrin.h\>.

\_evaluateDelayed() - Evaluates an input, and makes texU and texV available during that evaluation. inputVar must be a color input variable for the OSL shader. See \"Using delayed input textures\" below.

color \_evaluateDelayed(

color inputVar,

float texU,

float texV)

\_gaussian() - Returns a Gaussian spectrum, normalized so that the maximal value is 1.0. The useful ranges for the inputs are:

mean: 380 nm - 720 nm

sigma: 0 - 250 nm

The returned color is represented as a spectrum.

color \_gaussian(

float mean,

float sigma)

\_squareSpectrum() - Returns a spectrum that is 1.0 between begin and end, and 0.0 otherwise.

color \_squareSpectrum(

float begin,

float end)

\_triangularSpectrum() - Returns a triangular spectrum that is 1.0 at mean, and reaches 0 at mean +/- spread.

color \_triangularSpectrum(

float mean,

float spread)

\_spectrum() - Makes a spectral color. The four inputs correspond to the intensities at the wavelengths returned by getattribute(\"color:wavelengths\", wl).

color \_spectrum(

float a,

float b,

float c,

float d)

wavelength_color() - wavelength_color(float wavelength) returns a spectrum consisting of a narrow band around wavelength. Colors returned for wavelengths outside (390, 700) will be close to black. OctaneRender® converts this call to \_triangularSpectrum(wavelength, 30.0).

blackbody() - blackbody(kelvins) has the same meaning as in standard OSL, but returns a spectral color.

\_hueshift() - Shifts the hue of the given color. This is a circular shift. When shift = 6, this represents a full circle. The returned color is represented in the same way as the c argument. For RGB colors, 1 shifts red to yellow, while 2 shifts red to green. For spectral colors, colors shift to lower or higher wavelengths. OctaneRender® samples a limited number of wavelengths, so color fidelity will be rather low.

color \_hueshift(

color c,

float shift)

To learn more about programming with the [Open Shader Language](javascript:void(0);), refer to [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).
