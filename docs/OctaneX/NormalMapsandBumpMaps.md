Normal maps and Bump maps both serve the same purpose.  By using a Bump or Normal image, the geometry of the surface can have the appearance of more detail. This should not be confused with displacement mapping where the image used affects the geometry.

Bump maps are often greyscale images, and OctaneRender® uses the values to determine how much to affect the geometry at that location of the pixel.

Normal maps work different. They are color images that use RGB values to add directionality to the raised or lowered areas.

In OctaneRender®, the normal map is interpreted in tangent space. The X-axis is the tangent vector in the dP/dU direction, the Y-axis is the other tangent vector and the Z-axis is the normal direction.

 

#### FAQ

##### My Normal Maps From Z-Brush® Don' t Export Properly. What Can I Do?

To get Z-Brush® Normal maps to work in OctaneRender®, you must enable the Flip G button under the Normal Map settings and the Flip V button on the File Export .

![](images/normalmapsandbumpmaps1.png)

Figure 1: Z-Brush® Normal Map settings

![](images/normalmapsandbumpmaps2.png)

Figure 2: The Flip V button
