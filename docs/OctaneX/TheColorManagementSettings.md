The Color Management options allow for display color management to be activated or deactivated. There are numerous preset that can be selected from the Display Color Profile drop box for each monitor connected to the system (Figure 1). Additionally, OctaneRender® has implemented the Academy Color Encoding System (ACES), which uses the Open Color IO (OCIO) color management standard.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_10.png)        | Color management                                |
|                                   |                                                 |
|                                   | ![](images/Color_Management_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: Accessing the Display Color Management options.

Octane now has an option to select a built-in ACES color space. This can be enabled in the Tone Mapping section under the camera Imager parameters (figure 2).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_678.png)       | Built-In ACES Tone Mapping                      |
|                                   |                                                 |
|                                   | ![](images/Color_Management_Fig02_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 2: Enabling the built-in ACES tone mapping

Custom OCIO color profiles can be loaded as OCIO config files from the Use Other Config Files option in the Color Management preferences (figure 3). 

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_679.png)       | Importing OCIO Config Files                     |
|                                   |                                                 |
|                                   | ![](images/Color_Management_Fig03_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 3: Importing custom OCIO config files

The ACES profiles contained in the imported OCIO config file will be available in the camera Imager node under the OCIO settings (figure 4).

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_680.png)       | Choosing Custom OCIO Profiles                   |
|                                   |                                                 |
|                                   | ![](images/Color_Management_Fig04_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 4: Selecting ACES color profiles in the camera Imager node
