The Output AOV Parameter node works in conjunction with an Output AOV Texture node\'s Add Parameter option (figure 1). Adding parameter pins to an Output AOV Texture node provides inputs from other Output AOV nodes that can be called by the Output AOV Parameter node somewhere else in the Output AOV node network. 

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_279.png)       | Output AOV Parameter                                |
|                                   |                                                     |
|                                   | ![](images/Output_AOV_Parameter_Fig01_SE_v2026.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: Adding parameter pins to an Output AOV Texture node

 

In figure 2, a Wireframe AOV pass (parameter 1) is compositied on top of the Beauty AOV (parameter 0) using a Z-depth AOV pass (parameter 2) as the blend value for the Range node. 

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_665.png)       | Output AOV Parameter                                |
|                                   |                                                     |
|                                   | ![](images/Output_AOV_Parameter_Fig02_SE_v2026.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 2: An Ouput AOV Parameter node network sample
