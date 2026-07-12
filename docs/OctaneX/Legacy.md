The Legacy Output AOV nodes provide two nodes for backwards compatability in the compositing tree. The Apply Imager and Post Processing node can be used to adjust imager and post processing parameters specified in a compositing tree. More information on each parameter can be found in the [Post Processing](Post-ProcessingNode.md) and [Imager](ImagerSettings.md) articles. The Legacy Output AOV node provides options for output AOVs simliar to the Render AOV node used in the current compositor system. 

#### Legacy Output AOV Parameters

Enabled - Determines whether the node is active or not.

Input - Provides a list of all the render AOV nodes that can be added to a compositor tree.

Output Channels - Determines the channels to be used for the render AOV.

Enable Imager - If enabled, applies the imager settings on the final AOV output. 

Enable Post Processing - If enabled, applies the post processing settings on the final AOV output.

Enable PostFX Media Rendering - If enabled, applies the PostFX Media Rendering settings on the final AOV output.

Mask - Determines the node to be used for masking.

Mask Channel - Determines the channel in the mask input to be used for masking. 

Invert - Inverts the input of the node.

Scale - Sets the scale factor for the input\'s RGB values. 

Color Multiplier - Specifies a color to be multiplied with the input color. 

Opacity - Specifies the opacity channel used to control the transparency of this layer. 

Blend Color Space - The color space in which to apply blending and compositing.

- Linear sRGB - Blending and compositing will be performed in the linear sRGB color space. This is more likely to match compositing software, and is more physically accurate.
- sRGB - Blending and compositing will be performed in the sRGB color space. This is more likely to match image painting/manipulating software.

Blend Mode - The blend mode used to combine the input from this layer with the lower layer.

Alpha Operation - The alpha operation between this layer and the lower layer.
