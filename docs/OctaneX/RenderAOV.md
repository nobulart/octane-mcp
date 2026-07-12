The Render AOV node connects to a Output AOV node. It provides access to AOVs generated from the nodes available in the Node Graph Editor\'s Render AOVs category . There must be corresponding render AOVs for each Render AOV node connected to an Output AOV node (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_487.png)       | render aovs                               |
|                                   |                                           |
|                                   | ![](images/Render_AOV__Fig01_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Render Output AOV node compositing direct and indirect information generated from corresponding AOVs connected to the Render Target node

The Render AOV nodes need to have the associated AOVs selected from the Render AOV parameter list (figure 2).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_488.png)       | Specifying AOVs                           |
|                                   |                                           |
|                                   | ![](images/Render_AOV__Fig02_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: Specifying the appropriate AOVs in the Render AOV node\'s Render AOV parameter

Additionally, the Blending Settings on these nodes is where the blending type is specified for compositing (figure 3).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_490.png)       | Blending Settings                         |
|                                   |                                           |
|                                   | ![](images/Render_AOV__Fig03_SE_2023.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 3: Setting the Blending Settings parameter to Add for the Reflection AOV
