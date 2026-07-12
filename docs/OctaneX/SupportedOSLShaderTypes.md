OctaneRender® supports a subset of the OSL standard, plus a few extensions to use features specific to OctaneRender®.

 

#### Unsupported Features

- - Point cloud functions.
  - Dictionary lookup functions.
  - Message passing is generally not supported, except for the built-ins listed under \"Octane extensions\" (see below).
  - Derivatives.
  - trace(). For AO like effects, you can add a color input and connect the input pin to a Dirt node.
  - [Material](javascript:void(0);) shaders and closure variables.
  - wavelength color(). Use \_gaussian() instead.
  - struct variable types.
  - The global variables Ps and dPdt.

 

#### Partially-Supported Features

- - noise() doesn\'t support 4D noise, and doesn\'t support the Simplex and Gabor noise types.
  - The global variable time always has a value between 0 and 1, and represents the time within a subframe.
  - getmessage() and gettextureinfo() must have string literals as attribute names.
