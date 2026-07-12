The Sharpen Output AOV node can be used to sharpen components of a composite node tree (figure 1).

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_574.png)       | Sharpen                               |
|                                   |                                       |
|                                   | ![](images/Sharpen_Fig01_SE_2024.jpg) |
+-----------------------------------+---------------------------------------+

Figure 1: The Sharpen Output AOV node used to sharpen the output of a composite node tree

### Sharpen Parameters

Enabled - Determines whether the effect is active or not.

Strength - The amount by which to increase the sharpness. The equation is Output=Input+(Input-Blurred)\*Strength.

Radius - Determines the standard deviation of the Gaussian blur used for the unsharp mask, as a proportion of image width or height (whichever is larger).
