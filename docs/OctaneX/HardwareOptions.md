The options for adding GPU muscle to a computer depends on its available PCI-E slots. OctaneRender® can handle 200 concurrent GPUs with enterprise all access as long as they\'re set up as CUDA® devices. It does not need to be SLI-enabled to detect additional GPUs in the machine, and it is not recommended for render engines - OctaneRender runs much better without it because it can\'t differentiate GPUs accessible from the local area network or in the PC\'s PCI-E slots.

### Single PCI-E Slot

If the computer has a single PCI-E slot, there are not many options to extend rendering performance. You could add a more powerful GPU, as long as the power supply can provide enough power for it. Dual-GPU, single-slot card solutions can work, assuming that the power supply is sufficient to power the video card.

![](images/HardwareOptions_570x283.png)

Figure 1: Single PCI-E slot configuration

### Two Or More PCI-E Slot Motherboards

If the computer has two PCI-E slots, then you have more expansion options. If the power supply is sufficient, you can dedicate one GPU to the OS display, and then dedicate two or more GPUs for rendering. For the smoothest user experience with OctaneRender, we recommend dedicating one GPU for the display and OS to avoid slow and jerky interaction and navigation. The dedicated video card could be a cheap, low-power card since it will not be used for rendering, and it should be disabled under CUDA devices in Device Manager \> Preferences.

In this situation, we recommend matching the rendering GPUs in model and VRAM size. You can do multi-GPU rendering, but the OS interface may still be slow as all the GPU processing power is dedicated to the rendering process. In multi-GPU setups, the amount of RAM available to OctaneRender is not equal to the sum of the VRAM on the GPUs, but it is restricted to the GPU with the smallest amount of VRAM. We recommend disabling GPUs that don't have enough VRAM in order to render large scenes that can fit in the remaining GPU\'s VRAM.

![](images/HardwareOptions1_555x337.png)

Figure 2: Multiple PCI-E slot configuration

### Networked Primary Node And Render Nodes

If a local area network is available, then you have many additional upgrade options. However, this requires each Render Node machine in the network to have its own designated OctaneRender license. Just like in a multi-GPU setup, it is best to have the GPUs match in model and VRAM size. You can do multi-GPU rendering, but the OS interface may still be slow as all the GPU processing power is dedicated to the rendering process. The amount of RAM available to OctaneRender is not the total amount of VRAM from your GPUs, but it is the amount of VRAM from your smallest GPU. We recommend disabling GPUs that don't have enough VRAM in order to render large scenes that can fit in the remaining GPU\'s VRAM.

![](images/HardwareOptions2_665x475.png)

Figure 3: Networked GPU configuration

### Multi-GPU Setups, Power Supply, And Energy Consumption Considerations

It is important to use a suitable power supply when using multiple GPUs. For more info on what power supply is best for your case, visit [http://www.nvidia.com/object/slizone_build_psu.html](http://www.nvidia.com/object/slizone_build_psu.md). The differences in the micro-architecture of the cards should also be considered. For instance, the Kepler cards have more memory and consume less power than Fermi GPUs, but are just as fast with OctaneRender. Newer cards in the Maxwell and PascalTM series are also more power-efficient.
