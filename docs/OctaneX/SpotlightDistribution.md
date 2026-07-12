The Spotlight Distribution node can be used with an Octane Area Light or as part of an emission material on a polygon to create a realistic spotlight behavior, without the need of an [IES](javascript:void(0);) texture (figure 1).

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_281.png)       | Spotlight Distribution                                |
|                                   |                                                       |
|                                   | ![](images/Spotlight_Distribution_Fig01_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: The cube object on the is a normal emissive object with the spotlight distribution node attached

 

### Spotlight Distribution Parameters

 

Orientation- Determines how the cone will be oriented; the choice will use the coordinates in the Direction or Target edit fields.

- - Surface Normal
  - Direction - world space
  - Direction - object space
  - Target point - world space
  - Target point - object space

Direction or Target - The direction of the light or the target object.

Cone Angle - The angle of the actual cone. Smaller values produce a tighter cone.

Hardness - Sets the hardness of the penumbra (cone) boundaries. Lower values produce a softer look.

Normalize Power - Keeps the emitter angle constant when the angle changes.
