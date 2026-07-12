The Layered material system lets you construct complex materials that consist of a base layer and up to eight [Material](javascript:void(0);) Layers. The Layers are based on components used in previous Octane materials. Using this set of unique layers, OctaneRender® now lets you recreate complex materials in a physically-based manner, as opposed to manually [mixing materials](javascript:void(0);) together.

The following Material Layer nodes are available:

- [Diffuse](javascript:void(0);) Layer - Used for dull, non-reflective materials.
- Material Layer Group - Adds multiple Material Layers to existing materials.
- Metallic Layer - Used for highly reflective materials.
- Sheen Layer - Simulates the grazing coloration in fabrics.
- [Specular](javascript:void(0);) Layer - Used for shiny materials like plastic, or clear materials like glass.
- Material Layer Switch - This node can be used to connect two or more material layer types to one input on a Layered Material node.

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_93.png)        | Material Layers                                |
|                                   |                                                |
|                                   | ![](images/Material_Layers_Fig01_SE_v2024.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: Accessing the Material Layers from the Node Graph Editor window.

Material Layers can connect to the Layered Material, Layer Group, or Material Layer pins on standard materials.
