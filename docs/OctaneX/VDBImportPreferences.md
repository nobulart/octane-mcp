You can manage VDB import preferences under File \> Preferences \> Geometry Import \> VDB.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_18.png)        | VDB import                                            |
|                                   |                                                       |
|                                   | ![](images/VDB_Import_Preferences_Fig01_SE_v2023.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: VDB import preferences

### VDB Import Preferences

Length Unit - Tells OctaneRender® the unit of measurement used in the volume. The default unit is in meters.

Levelset Iso-Value - Sets the surface thickness of level sets, which are an encoding to store a thin eggshell surface.

VDB Grid Mapping - Allows for the selection of grids used for absorption, scattering, and emission. These mappings are only used with the Volume Medium, not the Standard Volume Medium node. The Standard Volume Medium node has it\'s own grid parameters listed by name for the various channel inputs. Please see the [Standard Volume Medium](StandardVolumeMedium.md) topic in this manual. 

Motion Blur Enabled - OctaneRender supports importing individual vector components to form velocity vectors for volume motion blur. You can load three float channels and have OctaneRender convert it to a vec3 velocity grid.

Scale - Selects the unit of measurement used in the volume file. The default unit is in Meters.

Vector Grid -One of two methods for selecting the velocity grid used for motion blur. The other method being the Component Grid. This method only lists Float3 grids with the velocity values in the x/y/z directions.

Component Grid -One of two methods for selecting the velocity grid used for motion blur. The other method being the Vector Grid. This method provides three separate float grids to load the corresponding x/y/z values.
