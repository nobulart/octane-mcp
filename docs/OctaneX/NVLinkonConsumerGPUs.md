NVLink lets you double your VRAM by combining two cards into one pool of fast shared (not mirrored) memory. NVLink® works with two cards, both of which need to be Quadro® or Geforce® RTX cards. Make sure that you use the bridge over your cards (Figure 1), otherwise you may experience a large performance drop.

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_529.png)       | NV LINK                           |
|                                   |                                   |
|                                   | ![](images/NVLink_Bridge_sm.png)  |
+-----------------------------------+-----------------------------------+

Figure 1: Example of a 3-slot NVLink® bridge connecting two Quadro® cards

To use NVLink with non-Quadro GPUs, enable SLI mode from the NVIDIA® Control Panel.

To use NVLink with Quadro GPUs, set the GPUs as Tesla Compute Cluster (TCC) devices. You can do this from the command line window with administrative privileges by running the nvidia-smi command within the NVSMI default folder ( C:\\Program Files\\NVIDIA Corporation\\NVSMI). The nvidia-smi command generates a table that displays your GPUs and what mode they are using (Figure 2).

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_530.png)       | Command Line                      |
|                                   |                                   |
|                                   | ![](images/nv-smi.png)            |
+-----------------------------------+-----------------------------------+

Figure 2: Table showing the devices in the machine, including the GPU ID and the mode of each device

To change the mode, use the following syntax in the command line:

nvidia-smi -g {GPU_ID} -dm {0\|1}    

Where, 0 = WDDM and 1 = TCC.

### Examples

This command switches the first Quadro GPU to WDDM mode:

C:\\Program Files\\NVIDIA Corporation\\NVSMI\\nvidia-smi -g 0 -dm 0

This command switches the first Quadro GPU to TCC mode:

C:\\Program Files\\NVIDIA Corporation\\NVSMI\\nvidia-smi -g 0 -dm 1

When the devices are set and NVLink is installed, you can combine p2p video memory. This is evident in the OctaneRender Devices tab under File \> Preferences (Figure 3). The device\'s Preferences window shows status info per device (Figure 4), not the total VRAM memory combined. OctaneRender uses p2p when the the primary device\'s VRAM is maxed out (Figure 7).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_585.png)       | Peers                                     |
|                                   |                                           |
|                                   | ![](images/NVLink_fig3_SEv2019_1_XB2.png) |
+-----------------------------------+-------------------------------------------+

Figure 3: You can specify VRAM pooling peers for NVLink-enabled devices

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_586.png)       | Device Info                               |
|                                   |                                           |
|                                   | ![](images/NVLink_fig4_SEv2018-1_RC6.png) |
+-----------------------------------+-------------------------------------------+

Figure 4: Device Info in the Preferences window shows info per device

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_587.png)       | Settings Peers                            |
|                                   |                                           |
|                                   | ![](images/NVLink_fig5_SEv2019_1_XB2.png) |
+-----------------------------------+-------------------------------------------+

Figure 5: Setting the peers for the NVLink®-enabled devices

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_588.png)       | Peered Devices                            |
|                                   |                                           |
|                                   | ![](images/NVLink_fig6_SEv2018-1_RC6.png) |
+-----------------------------------+-------------------------------------------+

Figure 6: An example showing that device 1 is peered to device 2 and vice-versa

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_589.png)       | Ram Usage                                 |
|                                   |                                           |
|                                   | ![](images/NVLink_fig7_SEv2018-1_RC6.png) |
+-----------------------------------+-------------------------------------------+

Figure 7: P2P is used when the primary device\'s VRAM is maxed out

+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                       |
|                                                                                                                                                                                                            |
| You cannot connect a display or monitor to the GPU adapters when the underlying devices are running in TCC mode. This causes unpredictable behavior, and may result in having to reboot the entire system. |
+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
