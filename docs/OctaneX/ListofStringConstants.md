#### Supported Operations On String Values

OctaneRender® considers strings to be opaque values, and supports only a limited set of operations:

- - Assignment (string b = a;)
  - Check for equality (a == b, a != b)
  - Using strings as arguments in functions and shaders

OctaneRender®doesn\'t support any of the standard string functions defined by OSL.

 

#### Types Of String Variables

OctaneRender® distinguishes between three types of string variables:

- - File names: These are strings passed into image sampling functions, like texture().
  - Enum values: These are strings passed into functions that take a well-defined set of possible values, like raytype() or noise().
  - Other strings: Strings that are not used for either of the above, or are used for multiple types of enums.

The Octane OSL compiler uses static code analysis to determine how it uses each string variable. If a variable is used as both an enum value and a file name, a compiler error is raised.

 

#### Using Strings As Shader Inputs

OctaneRender® represents the three string types above with different widgets:

- - A file name is always shown as a file input, and any metadata is ignored.
  - Enum values will by default be represented by an Enum input pin.
  - Other string values will by default be represented by an Enum input pin.

 

#### String Literals In Texture() Calls

If the argument of a texture call is a constant string, the compiler generates a file name input and uses the literal value as the default value. This loads OSL code, which contains file names, and ensures any referenced files are packed when you export a scene to [ORBX](javascript:void(0);)®.

To learn more about programming with the [Open Shader Language](javascript:void(0);), see [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).
