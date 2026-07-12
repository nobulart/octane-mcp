OctaneRender® supports camera movement with a 3D mouse on all platforms. The movement is camera-centric; movements you make translate into camera movements.

### Installation

On Windows®, driver installation isn\'t required to work with OctaneRender, and installing the 3D mouse is straightforward.

To install the mouse on Linux:

1.  1.  Install libmotif3 (or libmotif4 if that version is not available).
    2.  Download [3DxWare for Linux](2.%203DxWare%20for%20Linux).
    3.  Install the driver. Refer to the installation instructions in the package for details.
    4.  Start the driver as root.
    5.  Start OctaneRender, or if it is already running, lock and unlock the Viewport.

If the 3D mouse requires drivers, you can download them from <https://3dconnexion.com/us/drivers/>.

### Setup

Make sure you\'ve installed the correct drivers for your 3D mouse. On Windows® and Mac®, your 3D mouse should work after you plug it in to your computer. On Linux, make sure the driver is running before you start OctaneRender. If you start the driver later, lock and unlock the Viewport to detect the 3D mouse. On Windows, the settings from the 3Dconnexion control panel have no effect. You can change the speed of the movements and invert settings from File \> Preferences \> Controls in OctaneRender (figure 1).

+-----------------------------------+--------------------------------------------------+
| ![](images/NewItem_584.png)       | 3D Mouse PArameters                              |
|                                   |                                                  |
|                                   | ![](images/3DconnexionSpacenavigator_542x72.png) |
+-----------------------------------+--------------------------------------------------+

Figure 1: 3D Mouse parameters

+-----------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                              |
|                                                                                                                                   |
| The speed of translation is also dependent on the distance between the camera position and target. Zoom with the mouse to change. |
+-----------------------------------------------------------------------------------------------------------------------------------+
