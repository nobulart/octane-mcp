The Vectron Displacement  node displaces a Vectron or a Volume SDF with an input texture. It functions in real time, at any scale, and is compatible with complex SDF trees or Mesh Volume SDF nodes. A field texture can be used to limit the area of action (figure 1). 

+-----------------------------------+----------------------------------------------------------+
| ![](images/NewItem_667.png)       | Vectron Displacement                                     |
|                                   |                                                          |
|                                   | ![](images/Vectron_Displacement_disp_Fig01_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------------+

Figure 1: Examples of Vectron Displacement

The Vectron Displacement node can be accessed from the Geometry section in the Node Graph Editor window (figure 2). 

+-----------------------------------+----------------------------------------------------------+
| ![](images/NewItem_668.png)       | Vectron Displacement                                     |
|                                   |                                                          |
|                                   | ![](images/Vectron_Displacement_Disp_Fig02_SE_v2026.jpg) |
+-----------------------------------+----------------------------------------------------------+

Figure 2: Accessing the Vectron Displacement node

### Vectron Displacement Parameters

Bounds - Determines the bounds of the Vectron geometry in meters.

Input - The Vectron object to be displaced.

Texture - Determines the value for displacement, usually a texture map. 

Height - Amplitude of the displacement, inward or outward. 

Offset - Moves the base surface inward or outward. 

Step Scale - The scale factor applied to the marching step. If the distance field is highly distorted, use a lower value to avoid steep gradients in the result.
