The Decal system is designed to allow for decals or stickers to be placed on scene objects. The system consists of the Decal Geometry node and the Decal Texture node. The Decal Texture node is used between existing connected texture maps and texture map input pins on an Octane material. This node communicates with a Decal Geometry node connected to the host geometry via a Geometry Group node. Figure 1 illustrates how a basic decal system is set up in the Node Graph Editor window. A Placement node is used to allow for easier manipulation of the placement of the decal. 

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_666.png)       | Decal Texture                                |
|                                   |                                              |
|                                   | ![](images/Decal_Texture_Fig01_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------+

Figure 1: Using the Decal geometry node and the Decal texture node to add a decal to a scene object

### Decal Geometry Parameters

Add Input - Adds a new texture input slot.

Priority - Determines which decal has priority when multiple decals overlap on a surface. 

Wireframe Color - Color of the decal wireframe. The wireframe along the boundaries helps with aligning the decal in 3D space. This feature can be enabled in the render viewport window. 

UV Transform - Provides basic UV transformations for the decal depending on the projection type set in the connected texture map input.

Opacity - Determines the opacity for the connected texture map. 

Normal - Determines the normal channel for the decal. This channel can be used to override the target\'s normal channel. 

Texture Input - The texture input slot where texture maps can be connected as decals. 

### Decal Texture Parameters

Base Color - Determines the base color underneath the decal or decals. This input pin can also accept other texture maps. 

Decal Texture Index - Specifies which Texture Input to use from the Decal Geometry node. 

Blend Mode - Determines the blend mode used to mix the decal texture with the base color or texture.
