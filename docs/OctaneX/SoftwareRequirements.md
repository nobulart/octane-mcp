### Windows® and Linux Requirements

To install OctaneRender® on Windows®, make sure you install the appropriate drivers for your GPU. After this, you only have to run the installer.

- OctaneRender is a CUDA® 10 application that requires an NVIDIA® graphics driver version 388.x or higher.
- OctaneRender for Linux (64-bit) is built and tested on Ubuntu 10.04 using GCC 4.4.3. This requires Linux installations with glibc 2.11.1 or higher, and libstdc++ of 4.4.3 or a Linux distribution more recent than end of 2009 with CUDA 9.1 or higher.
- You can download the latest video card drivers for Windows and Linux here: <http://www.nvidia.com/Download/index.aspx>

### macOS® Requirements

OctaneRender supports macOS® 13.3.x Ventura or later, and it requires an Apple M1or newer GPU (MacOS 13.1+, iOS and iPad OS 17+).

#### NVIDIA cuDNN Library File

OctaneRender requires NVIDIA CuDNN to run. You can download the cuDNN library file from here:

<https://render.otoy.com/downloads/ef/08/f5/63/cudnn_8_0_4_win.zip>

The library file should be placed in the either of these folders:

C:\\Users\\\[user\]\\AppData\\Local\\OctaneRender\\thirdparty\\cudnn_8_0_4\\

or

C:\\Program Files\\OTOY\\\[OctaneRender Studio+ 2022.1\]\\ 

### Downgrading Drivers

Some drivers are released in a beta state and may cause errors when running OctaneRender. You can revert to the previous driver by downgrading or installing an earlier but more suitable driver version.

#### Windows

After downloading a suitable driver from https://www.nvidia.com/Download/index.aspx, use [DDU](https://www.guru3d.com/download/display-driver-uninstaller-download) to remove the installed driver, then perform a clean installation of the preferred driver.

#### Linux

A driver downgrade is complex on Linux systems, and this should be done if the installed driver causes errors. If you need to downgrade your video driver, uninstall the current driver before installing the earlier version.

To determine the currently installed driver, find the nvidia-smi module and run it in command line. Check the article at linuxconfig.org called \"How to check NVIDIA driver version on your Linux system\" [(]((https://linuxconfig.org/?p=767)<https://linuxconfig.org/?p=767>) for other options to determine the current installed driver. Also make sure to consult the files that came with the current driver to learn how it was installed. If the current driver was installed using the apt command, the sudo apt-get purge nvidia\* command should remove all of the former drivers. Use apt commands if the current driver was installed through apt.

Download a suitable driver from [https://www.nvidia.com/object/unix.html](https://www.nvidia.com/object/unix.md), then prepare to uninstall the current driver. To avoid issues, check the installation files of the current NVIDIA® driver for the install/uninstall instructions as these will contain helpful commands such as:

\$ sudo nvidia-installer \--uninstall

Use the following command for more options:

\$ nvidia-installer \--advanced-options

Once uninstalled, reboot once before installing the preferred driver.
