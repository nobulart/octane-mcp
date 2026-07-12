The Gradient Map texture produces a gradient blend between colors. It accepts an input to determine how the gradient maps to the surface. In Figure 1, a gradient that goes from green to red connects to the [Diffuse](javascript:void(0);) channel of an OctaneRender® material. OctaneRender maps the gradient using a Falloff map, resulting in the reddish color of the gradient being more visible on the edges of the surface that face away from the camera, and the green color appearing on the parts of the surface that face the camera. This node can be used in conjunction with the Gradient Generator node to create various gradient shapes such as radial or polygonal.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_262.png)       | Gradient Map                                      |
|                                   |                                                   |
|                                   | ![](images/Gradient_Texture_Fig01_Nuke_v2020.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: A Falloff map is mapping a colored gradient to a surface

 

### Gradient Map Parameters

Gradient Map - Determines the gradient\'s colors. Use the + and - buttons to add or remove gradient markers. Each new marker creates an arrow and a new color input option. You can place the color on different parts of the gradient by dragging the marker around.

Interpolation - Select Constant, Linear, or Cubic to determine the color-blending rate from one marker to the next.

Input Texture - Determines how the color maps to the surface.

Start Value - Use the color swatches or RGB values to set the gradient\'s starting color.

End Value - Use the color swatches or RGB values to set the gradient\'s ending color.
