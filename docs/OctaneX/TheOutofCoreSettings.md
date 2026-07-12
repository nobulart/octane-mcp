The out-of-core feature lets you use more textures and geometry than would fit in VRAM by keeping them in RAM instead (Figure 1). The data for rendering the scene needs to go to the GPU while rendering, so some tradeoff in the rendering speed is expected. This also means that as the CPU accommodates requests to access the host memory, CPU usage increases, and any RAM occupied with out-of-core data isn\'t available to other applications. This holds true also for the Render Node nodes if the network rendering feature is deployed. If out-of-core textures are not used, the rendering speed is not affected.

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_13.png)        | out of core                                         |
|                                   |                                                     |
|                                   | ![](images/Out_of_Core_Settings_Fig01_SE_v2026.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: Accessing the Out-of-Core settings.

The out-of-core feature comes with another restriction - out-of-core data must be stored in non-swappable memory, which is limited. When the host memory is used up for out-of-core data, the system can not make room for other processes. Since out-of-core memory is shared between GPUs, you can not turn devices on or off while using the out-of-core feature.

You can enable and configure the out-of-core memory system from the Application tab in Preferences.

When using the out-of-core feature on Render Node through network rendering, you\'ll need enough RAM for the Render Nodes. For net Render Nodes, you can specify the out-of-core memory options during the daemon installation. When specifying this for the Render Nodes, the out-of-core memory amount should be entered in bytes, not gigabytes.

For example, if the Primary Node is rendering a large scene that has texture climbing up to 6 GB, the out-of-core memory amount to specify for the Render Nodes during the Render Node daemon installation would look like this:

octane_node.exe \--net-master-address 192.168.xxx.xxx \--net-master-port 21000 \--out-of-core 6442450944

With the added support for out-of-core geometry in OctaneRender®, you can use a significant portion of the system memory for geometry data. You can utilize multiple GPUs in conjunction with the out-of-core feature.

### Out-Of-Core Preferences

Enable Out-Of Core Data - When enabled, OctaneRender®uses out-of-core data when a scene does not fit in VRAM.

System RAM Usage Limit \[GB\] - Limits how much system memory OctaneRender® uses for out-of-core geometry and textures. Once texture or geometry data is placed on this amount of RAM and the out-of-core feature kicks in, this specific memory is not accessible by the operating system for other tasks.
