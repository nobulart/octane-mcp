You can specify any of the environment nodes (Daylight, Texture, or Planetary) to be an environment for lighting or the background. Apart from having an HDR image to light the environment, you can specify a different environment for the background and see that background in reflections.

If one of these environment nodes is connected to the Visable Environment pin on a Render Target node, this environment is used for reflections, refractions, and all camera rays that leave the scene. The regular environment is used just for the direct light calculation.

The Visible environment overrides the normal environment in some specific use cases, giving more control over the final look of the render. If you configure a Medium in the environment, OctaneRender® ignores the medium when the environment is used as a Visible environment.

Environment nodes  have extra options controlling the environment\'s behavior when used as the visible environment. When the node is used as a normal environment, these options are ignored:

- - Backplate - Uses the Visible environment as a backplate image.
  - Reflections - The Visible environment overrides the Normal environment when calculating reflections for Specular and Glossy materials.
  - Refractions - The Visible environment overrides the Normal environment when calculating refractions for [Specular](javascript:void(0);) materials.

In the examples below, Daylight environment nodes are used for both environments, except the normal environment is at noon, while the visible environment is at sunset.

+-----------------------------------+--------------------------------------------+
| ![](images/NewItem_495.png)       | Visible Environment Examples               |
|                                   |                                            |
|                                   | ![](images/SunSkyEnvironment1_393x778.png) |
+-----------------------------------+--------------------------------------------+

Figure 1: Visible environment examples
