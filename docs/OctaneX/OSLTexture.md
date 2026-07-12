The OSL texture node is a scriptable node that lets you write scripts using OSL ([Open Shader Language](javascript:void(0);)) to define arbitrary texture types and create customized OctaneRender® materials and shaders. To learn about the generic OSL standard, please read the [OSL Readme](https://github.com/imageworks/OpenShadingLanguage/blob/master/README.md) and [PDF documentation](https://app.readthedocs.org/projects/open-shading-language/downloads/pdf/latest/).

An OSL script is written into the OSL texture node from the Script Editor window. Click on the Pencil icon to open the Script Editor. If the script exists as an external OSL file, click the Load icon to insert the OSL file into the node. You can edit any existing file used within an OSL texture node. To refresh the file after editing, click the Reload icon.

![](images/Osltexture_inspector_v3-08-4.png)

Figure 1: Reload icon

The OSL texture requires one output color. One OSL texture node is one OSL compilation unit, which contains only one shader. The OSL texture node has one Output attribute pin that connects to the Texture input pin of other Texture nodes (like Turbulence), or to the Texture input pin of Octane materials (like [Diffuse](javascript:void(0);)).

+-----------------------------------------------------------------------+
| NOTE                                                                  |
|                                                                       |
| Multiple outputs for OSL textures are not supported.                  |
+-----------------------------------------------------------------------+

OctaneRender® supports most of the texturing functions (like [Textures](javascript:void(0);) or Noises) in the OSL Specification.

When you invoke an OSL texture, it comes with an initial script that has declaration component and includes one output variable, which represents a color. The initial script's function body then initializes the color to black based on the standard RGB color mode. You can customize the script to create a customized OSL texture shader. A custom script may have many variables, some of which require input through the Input nodes. Depending on the custom script, the OSL texture may have an input of 0, or many Input nodes.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_647.png)       | Initial Script                                  |
|                                   |                                                 |
|                                   | ![](images/Osltexture_scriptarea_SEv3-08-4.png) |
+-----------------------------------+-------------------------------------------------+

Figure 2: An OSL texture node's initial script containing an OSL program code to calculate the output color

![](images/Osltexture_scriptareacompile_SEv3-08-4.png)

Figure 3: The Compile button

 

The example in Figure 4 below shows an OSL shader that adds two RGB textures.

Shader Add (

color a = 0,

color b = 0,

output color c = 0)

{

c = a + b;

}

The script's declaration component has three variables: two are input variables of Input Type color, and the third one is the required output represented by a variable of Output Type color. The OSL Input/Output Type color corresponds to an Octane Texture attribute node. The script's function body adds the two input parameters and places the result into the output variable.

For a list of OSL variable declaration Input/Output types in the OSL dpecification that OctaneRender supports, see the Appendix topic on OSL Implementation in OctaneRender in this manual. To learn more about scripting within OctaneRender using OSL, see the [The Octane OSL Guide](https://docs.otoy.com/osl/index.md). Figure 4 is an example of an OSL Texture node with an OSL script to add two Input texture nodes and send the result to one output

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_648.png)       | OSL Texture Example                        |
|                                   |                                            |
|                                   | ![](images/OSL_Texture_Fig04_SE_v2026.jpg) |
+-----------------------------------+--------------------------------------------+

Figure 4: An OSL example

 

Once the OSL texture is available, OctaneRender plugs it into a [Material](javascript:void(0);) node\'s Texture input pin. Similar to other Procedural texture types, it can replace its own initial attributes with other applicable texture types in the course of the texturing process. For example, the OctaneRender Texture attribute in Figure 3 is an RGB Color texture at first, but you can change it to any applicable OctaneRender texture from its representation on the Inspector node to further customize the OSL shader (Figure 5).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_649.png)       | Changing Inputs                                     |
|                                   |                                                     |
|                                   | ![](images/Osltexture_customizeinput_SEv3-08-4.png) |
+-----------------------------------+-----------------------------------------------------+

Figure 5: Changing the input node to customize the OSL shader

 

To learn more about the OSL implementation in OctaneRender, see the Appendix in this manual for more OSL-related topics.

+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                        |
|                                                                                                                                                                                                                             |
| When using OSL, make sure that shaders never lock up or run for a long time. This may cause the system to freeze, or the display driver resets. Some operations, like out-of-bounds array access, may cause kernel crashes. |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
