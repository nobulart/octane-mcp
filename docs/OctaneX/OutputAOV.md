The Output AOV node connects to the Output AOV Group node which is then connected to the Output AOVs pin on a Render Target node (figure 1). The Output AOV node is used to assemble results of the AOVs composited using Render AOV nodes (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_485.png)       | Output AOV Node                           |
|                                   |                                           |
|                                   | ![](images/Output_AOV_Fig01_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Output AOV Node used to composite a Diffuse and Reflection AOV

Multiple layers can be added via the Add Layer button. Layers can be removed with the Remove Layer button. When a layer is added, a new input pin will appear to the left of the current layer pin(s). Each set of Output AOV nodes are available for viewing in the Render Viewport when they are connected together using the Output AOV Group node (figure 2) 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_486.png)       | Viewing Output AOVs                       |
|                                   |                                           |
|                                   | ![](images/Output_AOV__Fig02_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: Viewing the results of an Output AOV node in the Render Viewport when connected to an Output AOV Group node
