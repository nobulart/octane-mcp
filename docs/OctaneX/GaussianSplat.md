OctaneRender® supports Gaussian Splat files which provide a representation of 3D scenes using a collection of Gaussians that approximate the geomtery and lighting of a captured scene (figure 1). Octane supports the .ply format for Gaussian Splat files. 

+-----------------------------------+----------------------------------------------+
| ![](images/NewItem_681.png)       | Gaussian Splat                               |
|                                   |                                              |
|                                   | Your browser does not support the video tag. |
+-----------------------------------+----------------------------------------------+

Figure 1: An example of a Gaussian Splat file imported into Octane

### Gaussian Splat Parameters

Tint Color - Adds an overall color tint to the scene. 

Alpha Min - Regions of the gaussian splat with alpha values smaller than this value will be invisible. Setting this value higher will produce better performance but worse visual quality.

Intensity - Adjusts the overall light intensity of the scene. 

Flip Axes - Inverts the gaussian splat\'s x and y axes. 

Object Layer - See the section on the [Object Layer](ObjectLayerNode.md) node for more details.
