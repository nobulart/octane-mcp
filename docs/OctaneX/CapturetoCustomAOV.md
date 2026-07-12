The Capture to Custom AOV node can be used to apply a texture to a custom AOV pass. Once a Capture to Custom AOV node has been connected to a material network, the custom AOV needs to be activated in the AOV tab for the Octane Render Target. See the section on AOVs for more information on using the Octane AOV passes (figure 1).

+-----------------------------------+------------------------------------------------------+
| ![](images/NewItem_273.png)       | Capture to Custom AOV                                |
|                                   |                                                      |
|                                   | ![](images/Capture_to_Custom_AOV_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------------+

Figure 1: The Capture to Custom AOV used to add the Fractal Noise pattern to the custom AOV matte

 

### Capture to Custom AOV Parameters

Capture Texture - The texture that is being captured and written to the custom AOV and forwarded to the destinations of the capture texture node.

Custom AOV - Specifies the custom AOV for the texture to be written to.

Override Texture - The texture specified here will be recorded in the custom AOV but the captured texture is still what is forwarded to the destination of the capture node.
