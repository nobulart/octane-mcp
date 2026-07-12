To set up OctaneRender® for offline use, you will need:

- A dongle
- DIT (Dongle Installer Tool)
- An internet-connected computer
- OctaneRender Standalone v3.08.3 or newer

Once you have the items, follow these steps:

1.  1.  Add your license to your dongle. Your OctaneRender standalone license is assigned to your dongle, pending activation. If you want to work offline with your OctaneRender plugin, you also need to assign the plugin license to the dongle.
    2.  Navigate to the Dongles tab in your OTOY® account. Click Add Licenses, and select the plugin license. Next, click Assign To Dongle.

+-----------------------------------+---------------------------------------+
| ![](images/NewItem_514.png)       | Dongle Tab                            |
|                                   |                                       |
|                                   | ![](images/donglesetup_fig1_SEv4.png) |
+-----------------------------------+---------------------------------------+

Figure 1: Information found in the your OTOY® account\'s Dongle tab

1.  1.  Download the [Dongle Installer Tool](https://render.otoy.com/account/dongles.php?) by clicking Install Licenses. You can select Windows®, macOS®, or Linux for the installer.

+-----------------------------------+-----------------------------------------------+
| ![](images/NewItem_515.png)       | Adding Licenses                               |
|                                   |                                               |
|                                   | ![](images/donglesetup_fig2_SEv4_764x213.png) |
+-----------------------------------+-----------------------------------------------+

Figure 2: Adding licenses to the dongle

1.  1.  Launch the Dongle Installer Tool, then log in with your OTOY credentials.
    2.  Click the checkbox in the Select column and click Install Selected. The installation may take a moment.

+-----------------------------------+------------------------------------------------------------+
| ![](images/NewItem_516.png)       | OToy Credentials                                           |
|                                   |                                                            |
|                                   | ![](images/OctaneRender_Dongle_Setup_Offline_Fig03_SE.jpg) |
+-----------------------------------+------------------------------------------------------------+

Figure 3: Entering your OTOY® credentials

+-----------------------------------+------------------------------------------------------------+
| ![](images/NewItem_517.png)       | Installing Licenses                                        |
|                                   |                                                            |
|                                   | ![](images/OctaneRender_Dongle_Setup_Offline_Fig04_SE.jpg) |
+-----------------------------------+------------------------------------------------------------+

Figure 4: Installing the added licenses for offline use

1.  1.  You can now remove the dongle and use it with your designated offline machine. To make sure the dongle works, launch OctaneRender®. When you click on File \> Activation Status, you should see Octane is activated using an Octane dongle at the bottom of the Activation Status window. You can add OctaneRender plugin licenses to the dongle at a later time by repeating steps 1 and 2 for each license.

+-----------------------------------+------------------------------------------------------------+
| ![](images/NewItem_518.png)       | Activation Status                                          |
|                                   |                                                            |
|                                   | ![](images/OctaneRender_Dongle_Setup_Offline_Fig05_SE.jpg) |
+-----------------------------------+------------------------------------------------------------+

Figure 5: OctaneRender activation status without an internet connection

1.  1.  You need to update dongles every four months with the Dongle Installer Tool. An error occurs during the update process if the licenses are still active so ensure to deactivate the licenses prior to updating the dongles. You can deactivate the license by signing out from the OctaneRender application\'s Activation Status dialog or by using the Unlock buttons from your online Otoy account. To update your dongle, run the Dongle Installer Tool, select the checkbox next to your dongle, then click Install Selected. Your dongle is now updated.

+-----------------------------------+------------------------------------------------------------+
| ![](images/NewItem_519.png)       | Updating Dongle                                            |
|                                   |                                                            |
|                                   | ![](images/OctaneRender_Dongle_Setup_Offline_Fig06_SE.jpg) |
+-----------------------------------+------------------------------------------------------------+

Figure 6: Updating a dongle

+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| By default, using the dongle in Linux systems requires sudo permissions. In order to get around this, copy the udev rules file, [99-senselock.rules](https://render.otoy.com/downloads/38/cb/19/5b/99-senselock.rules), into the udev rules directory. The udev rules directory is usually /etc/udev/rules.d, but this may vary across various Linux distributions. With the udev rules files in place, restart or force the udev daemon to reload the rules (udevadm control \--reload-rules). See the Debian documentation at https://wiki.debian.org/udev for more information |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
