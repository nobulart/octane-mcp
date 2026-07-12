The Relative Distance node converts the distance to the origin from one of the specified reference transformations into a greyscale texture (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_235.png)       | Relative Distance                                |
|                                   |                                                  |
|                                   | ![](images/Relative_Distance_Fig01_SE_v2023.jpg) |
+-----------------------------------+--------------------------------------------------+

Figure 1: Relative Distance node connected to the Diffuse pin on an Octane material

### Relative Distance Parameters

Distance Mode - Returns the Euclidean distance between the shaded point and the origin of the specified reference transform.

Reference Transform - Transform defining the coordinate system used to compute the distance metric.

Use Full Transform - If Enabled, the distances will be calculated after applying the full reference transform, including scale and rotation. If Disabled, only the translation is taken into account.

Normalize Results - Takes the result and normalizes the values between 0 and 1.

Normalization Range - Defines the minimum and maximum of the normalization range.
