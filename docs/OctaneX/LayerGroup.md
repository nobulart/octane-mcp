The Layer Group blend node can be used to group and blend various output AOV nodes together prior to being connected to an Output AOV node.This node further expands the blending and layering capabilities of the compositing system.In the following example, An Image File node and a Render AOV node are blended together and their result is composited using a Subtract blending setting. 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_539.png)       | Layer Group                               |
|                                   |                                           |
|                                   | ![](images/Layer_Group_Fig01_SE_2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Layer Group output AOV node used to blend an Image File node and Render AOV node

### Layer Group Parameters

Add Layer - Adds a new layer input to the Layer Group node.

Enable - Determines whether the Layer Group is active or not.

Blending Settings - Determines the blending mode for the entire Layer Group.

Layers - The individual layers connected to the Layer Group node.
