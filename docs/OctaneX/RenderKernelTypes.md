There are five types of Render [Kernels](javascript:void(0);) in OctaneRender®: Direct Lighting, Info Channels, PMC, Photon Tracing, and Path Tracing. The kernels are accessible by clicking on the Render Target button in the Node Inspector and choosing the kernel type from the Kernel parameter under the Render Settings rollout (figure 1).

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_427.png)       | Kernel Types                                       |
|                                   |                                                    |
|                                   | ![](images/Render_Kernel_Types_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: Kernel Types are found in the parameters for the Render Target

You can also place a Kernel node in the Nodegraph Editor and connected to the Kernel pin on a Render Target node (figure 2).

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_428.png)       | Adding KErnels in Node Graph      |
|                                   |                                   |
|                                   | ![](images/RenderKernel3.jpg)     |
+-----------------------------------+-----------------------------------+

Figure 2: Adding a Render Kernel node to the Nodegraph and connecting it to the Render Target

The Kernel node can be accessed by right-clicking in the Nodegraph Editor and choosing the Kernels category.There is a Kernel Switch node under the Utility section. This can be used to switch between different kernel types assigned to one Render Target node.

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_429.png)       | Accessing KErnel Nodes                             |
|                                   |                                                    |
|                                   | ![](images/Render_Kernel_Types_Fig03_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 3: Add a Render Kernel node using the context menu in the Nodegraph
