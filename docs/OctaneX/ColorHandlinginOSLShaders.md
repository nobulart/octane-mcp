An OSL shader corresponds to a Node in our node system. Input parameters show up as input pins on the OSL texture node. There is a single Output parameter corresponding to the output value of the node.

The I/O types in OSL code correspond to the following Octane attribute pin types:

color - Octane Texture attribute

point - Octane Projection attribute (UV, spherical, cylindrical...)

vector, normal - Octane Float attribute (X, Y, Z)

matrix - Octane Transform attribute

float - Octane Float attribute (1D-value)

int - Octane Int attribute (1D-value)

string - Octane Filename or Enum ⁽¹⁾ attribute

Default values in the function signature are used as the default values for the input pins.

OSL allows metadata for shaders that provide more control of how the node parameters display. OctaneRender® supports the following:

 

#### Metadata For All Inputs

string label - Overrides the name shown in the Node Inspector. Normally, the variable name is shown.

string help - Provides a tool tip for the pin when you hover your mouse over the pin.

string page - Groups pins into categories.

 

#### Metadata For Int And Float Inputs

float/int min, max - Specifies the minimum and maximum values for a Float or Int input. There\'s no guarantee that the actual value for the variable in the shader is inside these bounds.

float/int slidermin, slidermax - Specifies a narrower value range for the sliders. You can still enter values outside this range (but within min/max) by holding down the right mouse button, and by entering a value.

float/int sensitivity - Specifies the steps for a Float/Int type variable.

float/int sliderexponent - Sets up the skew factor for the slider. OctaneRender®, supports just the linear (sliderexponent == 1) and logarithmic (sliderexponent \> 1) are supported.

 

#### Metadata For Int Inputs

string widget = \"checkBox\" - Shows a checkbox instead of a slider. The input value will be 0 or 1.

string widget = \"boolean\" - Synonym for checkBox.

string widget = \"mapper\" - Turns the input value into an enum value (PT_ENUM), which OctaneRender® represents with a dropdown menu.

string options - Use a combo box. Options are separated by pipe characters, the keys, and value by a colon, e.g., option one:1\|option two:2\|option three:3.

 

#### Metadata For Matrix Inputs

int dim - Set to either 2 or 3, this specifies if the matrix should show as a 2D or 3D transform.

 

#### Metadata For String Inputs

string widget = \"popup\"/string options - Use a combo box, using the options in the given string. Options are separated by pipe characters, e.g., option one\|option two\|option three.

int editable - If set to 1, you can enter string values in a combo box that are not in the list of options.

File name inputs always displays as a file input, regardless of any given metadata.

To learn more about programming with the [Open Shader Language](javascript:void(0);), see the OSL guide here: https://docs.otoy.com/osl/
