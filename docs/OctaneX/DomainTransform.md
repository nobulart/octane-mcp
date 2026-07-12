The Domain Transform node provides adjustment parameters for Signed Distance Field (SDF) objects (figure 1).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_62.png)        | DOMAIN TRANSFORM                                |
|                                   |                                                 |
|                                   | ![](images/Domain_Transform_Fig01_SE_v2022.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: Applying the Domain Transform Vectron Operator to an imported SDF object

### Domain Transform Parameters

SDF - The Signed Distance Field object to evaluate.

P Transform - Provides translation, rotation, and scale values for the manipulation of the node results.

Projection - In the case of Vectron, there are no UV projections, therefore, the projection type provide additional shaping options based on traditional projection types. The default (XYZ to UVW) provides the most predictable results.

Bounds - Determines the bounds of the Vectron geometry.

Step Scale - The scale factor applied to the marching step. If the distance field is highly distorted, use lower values to avoid steep gradients in the result.
