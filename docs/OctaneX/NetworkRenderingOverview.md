Network rendering lets you utilize additional GPUs in other computers to render images. OctaneRender® distributes compiled render data and not scene data, so no file management is required. It is similar to working with additional GPUs by allowing the distributed rendering of single images over multiple computers connected through a fast local area network. Network rendering requires a Primary Node and one or more Render Nodes on different computers. The OctaneRender instance that drives the rendering is the Primary Node, and the OctaneRender® instances that help are the Render Nodes.

Since an OctaneRender® Render Node requires an activated Standalone license, we recommend running Standalone first to activate a Standalone license on that computer. It is best to copy the whole folder of the released archive onto the Render Node computer. Make sure that the Primary Node and Render Node are not blocked by any firewalls in the network or operating system.

 

### Primary Node, Render Nodes, And Daemons

 

The Standalone version or the octane.exe act as Primary Node and a special console version of OctaneRender, octane_node.exe, can run on other computers as Render Nodes. They should all be on different computers, or they would have to share the same GPUs.

The OctaneRender Primary Node does all the render data processing. The Render Node does not need to have a powerful CPU, but the Render Node needs enough RAM to store the render data plus some render results. The Render Node\'s operating systems can also be different since the communication between the machines is cross-platform. No data is stored on the Render Node's discs, it\'s all stored in memory.

Each time network rendering is required, the Render Node process has to launch on the Render Node machines. The Render Node daemon makes the control of the Render Nodes more practical, as it can launch at startup on each machine in the network. The daemon is the little program that starts a Render Node process on the machine on request by a Primary Node, monitors it, and stops it on request by a Primary Node. Monitoring means making sure that a running Render Node sends a regular heartbeat to the daemon, and if that doesn't happen, it first tries to stop the Render Node, and then it kills the process as a last resort if necessary. The daemon runs all the time, and starts/stops a Render Node process if a Primary Node requests it. The daemon also listens for the heartbeat of the Render Node to check if the Render Node process is still running. This Render Node daemon eliminates needing to launch the Render Node process manually on each computer each time rendering is required on the Render Node.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_400.png)       | Render Node Configuration                 |
|                                   |                                           |
|                                   | ![](images/NetOverview_v2020_601x344.png) |
+-----------------------------------+-------------------------------------------+

Figure 1: Primary Node - Render Node configuration

OctaneRender\'s network rendering feature is also useful while using Octane plugin editions. Any machine with an OctaneRender Enterprise license can become either a Primary Render Node for content creation or a helper render node. Meanwhile machines with only an OctaneRender Enterprise Render Node license can only be helper render nodes.

When using Octane plugin editions, OctaneRender Render Nodes can only be utilized in conjuntion with native OctaneRender distributed network rendering and will not work with third party render job management software, such as TeamRender or Deadline.

 

When a Primary Node invokes a daemon, the Render Node launches to get some information about the number of GPUs, version, bitness, etc., and closes again. After that there is no Render Node process running, so the daemon waits for Primary Nodes to detect it by scanning the complete local network in regular intervals. The daemon should appear in the daemon list of the network preferences of the Primary Nodes. If it does not, it could be because:

- The network rendering in the Primary Node is not enabled.
- The daemon is listening on a different port than the Primary Node is scanning.
- The daemon is in a different subnet than the Primary Node is scanning. If you have one ethernet adapter on the daemon and Primary Node PCs, you can ignore this case.
- The Windows® firewall keeps the Primary Node from connecting to the daemon, or the daemon from responding to the Primary Node. To verify it, disable the firewall on both PCs. If the daemon is now detected (this can take up to 20 seconds), you can try enabling one firewall after the other to see which one is causing trouble.

When you enable a daemon in the Primary Node\'s settings, the Render Node launches and appears in the Primary Node\'s status bar. One Primary Node can activate one daemon at a time. If daemon is occupied by another Primary Node, you will see the daemon state change accordingly. The automatic port configuration is an option on the Primary Node that enables the same computer to use multiple Primary Nodes.

+-----------------------------------+-----------------------------------------------------------+
| ![](images/NewItem_406.png)       | Network Rendering Tab                                     |
|                                   |                                                           |
|                                   | ![](images/Network_rendering_Overview_Fig02_SE_v2021.jpg) |
+-----------------------------------+-----------------------------------------------------------+

Figure 2: [Network Rendering](javascript:void(0);) tab

 

When network rendering is disabled, the local network is not scanned for daemons. The Primary Node scans for daemons only when network rendering is enabled.

 

### Maximum Number Of GPUs

OctaneRender (through the Primary Node) may use the networked GPUs as long as the number of GPUs do not exceed the limit set by the OctaneRender® license for that Primary Node. The OctaneRender® Enterprise license lets a Primary Node render with up to 200 GPUs at a time including the Primary Node\'s GPUs in the machine. For Studio licenses, a Primary Node can use up to two GPUs at a time.

In versions 3.05.0 and earlier, OctaneRender® looks for GPUs in Render Node nodes within the same subnet, so OctaneRender® treats every [GPU](javascript:void(0);) in the Primary Node and Render Nodes as if these are installed in the Primary Node machine. Each local and remote GPU in the Render Nodes is just another GPU, so as long as it is available (not used by other renderers or the OS or any other application) and it\'s exposed as a CUDA® GPU, OctaneRender® will pick those GPUs in that subnet until it reaches the GPU limit, if the network has more than the GPUs limit then the rest of the available GPUs will just not be used.

In OctaneRender v3.06.x and later, the native Octane Network Rendering feature has integrated support for multiple subnets and considers hostnames and IP addresses. The improved Network Render feature considers the per-Render Node systems that determine how GPUs are allocated to applications and the overall network system configuration that affect how networked nodes allocate processing capabilities between nodes. Depending on how the mix of configurations play out, there are some cases where a network allows OctaneRender® to use up to the GPU limit across the network, regardless what Render Nodes the GPUs are installed in (per GPU regardless of the Render Node), and there are also other cases where the network cuts off the other remaining Render Nodes when a Render Node will go over the GPU limit (so per Render Node rather than per GPU, this means it will use all GPUs in that Render Node or not use that Render Node at all) - effectively reducing the total rendering GPUs to significantly less than the limit.

In all versions of OctaneRender, there is always some hardware considerations, such as the node/GPU power density and heat loads within the Render Nodes that affect the availability and usability of each installed GPU.
