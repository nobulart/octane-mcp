The Trace Set system allows for greater control over including or excluding scene data from object surfaces when light hits the surface (figure 1). It is similar the visibility settings in the Object Layer node but provides a deeper level of control that can be used across multiple objects.

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_599.png)       | Trace Sets                                |
|                                   |                                           |
|                                   | ![](images/Trace_Sets_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: The Trace Set nodes used to filter out reflection and diffuse for a scene object

Objects can be added to a trace set by giving them a trace set name in the Trace Sets parameter under the Object Layer parameter set or in an Object Layer node attached to an object (figure 2). 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_600.png)       | Trace Set Name                            |
|                                   |                                           |
|                                   | ![](images/Trace_Sets_Fig02_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 2: Adding a Trace Set name to a scene object

The Trace Set names can then be called in a Trace Set Visibility Rule node (figure 3). The Trace Set Visiblity Rule node is connected to a Trace Set Visibility Rule Group node where multiple rules can be created. This node is then connected to the Trace Set Visibility Rules pin on an Object Layer node (figure 3). 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_601.png)       | Trace Set Node Setup                      |
|                                   |                                           |
|                                   | ![](images/Trace_Sets_Fig03_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 3: The Trace Set node setup for a scene object

### Trace Set Visibility Rule Parameters

Exclude - The trace set names to include, separated by commas. These set names are added to scene objects in the Trace Sets parameter under the Object Layer parameter set for each scene object. 

Reinclude - Comma-separated list of names of trace sets to be treated as visible again for future hits in light paths that hit objects with this trace set applied, after potentially having been excluded by an earlier bounce. 

Apply to Bounce Types - Determines the type of light path bounces to apply to objects in a named trace set. 

Apply to Future Hits - Determines how this trace set rule apllies to future light path bounces. 

- All Future Hits - After a bounce to which this rule applies, this rule will continue to apply. 
- Next Hit Only - This rule only applies when considering the next hit after the current bounce, and future hits will be treated as if this rule does not apply. 
- All Future Hits After Next Hit - This rule only applies when considering the future of light path hits after the next hit.

+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                                             |
|                                                                                                                                                                                                                                                  |
| Shadow bounces only continue for a single hit after the bounce. Therefore, for shadow bounces there is no difference between All Future Hits and Next Hit Only and the rule All Future Hits After Next Hit will never apply to a shadow bounce.  |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

### Trace Set Visibility Rule Group Parameters

Add Rule - Adds new rules to the trace set.

### Trace Set Visibility Rule Switch Parameters

Add/Remove Option - Adds or removes input pins for new trace set visibility rules.

Input - Determines which trace set visibility rule  input to utilize.

Inputs - The various trace set visibility rules are connected here.

### Trace Set Visibility Rule Group Switch Parameters

Add/Remove Option - Adds or removes input pins for new trace set visibility rule groups.

Input - Determines which trace set visibility rule group input to utilize.

Inputs - The various trace set visibility rule groups are connected here.
