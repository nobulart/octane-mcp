Texture Render Job renders a Render Target into an image that can be used by other Render Targets. This is a workaround for the limitation that OctaneRender® can render one Render Target at a time, and there is no system in place to render Render Targets as inputs of other Render Targets. You have to run the Texture Render Job first prior to using its result in a meaningful way.

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_426.png)       | Texture Render Job                   |
|                                   |                                      |
|                                   | ![](images/texturerenderjobFig1.png) |
+-----------------------------------+--------------------------------------+

Figure 1: A typical use of the Texture Render Job in the Nodegraph Editor
