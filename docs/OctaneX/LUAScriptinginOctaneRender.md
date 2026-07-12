[Lua](javascript:void(0);) scripting allows you to create your own scripts to automate workflows or augment certain procedures. Animation scripts store your settings per project, instead of globally, in the applications settings. Scripts can create nodes and render them without changing the current project. OctaneRender\'s Lua API has basic animation support and camera motion blur can be set from Lua.

The script editor creates, edits and saves new scripts, or opens existing scripts for editing. Detailed documentation about the available API modules is provided through the Lua API browser, and it is also available as an HTML page on our [HTML documentation script page](http://render.otoy.com/forum/viewtopic.php?f=73&t=37323).

If you are new to Lua, check out Programming in Lua online: [http://www.lua.org/pil/contents.html](http://www.lua.org/pil/contents.md).

 

#### Using the LUA API Browser

 

Scripts can create nodes and render them without changing the current project. OctaneRender\'s Lua API has basic animation support where camera motion blur can be set.

The Octane API exposes a single table (or module) called octane.

![](images/TheScriptMenuandLua1_494x381.jpg)

Figure 1: Octane module

 

The Octane table contains all the other modules such as octane.gui, which is the gui module in the API browser. In the GUI module, the Members column lists three kinds of items: Functions, Properties, and Constants.

The items listed under Constants are other tables that contain constants that act as function arguments. All these values are listed in the Description column.

![](images/TheScriptMenuandLua2_498x385.jpg)

Figure 2: Constants items

 

All the constants listed in the Octane module are a special case because these are also available in the Octane table itself.

![](images/TheScriptMenuandLua3_472x404.jpg)

Figure 3: Constants listed in the Octane table

 

The items under Functions describe all the functions in a module. The Create item describes a function in the GUI module, and the function call looks like: octane.gui.create(table). Functions in Lua have a number of parameters and a number of return values, but this one is simple: it has one parameter, and one return value.

![](images/TheScriptMenuandLua4_487x419.jpg)

Figure 4: A Create item in the GUI module

 

The description of parameters and return values follows the following pattern: it gives the type, and some name (this can be a user-defined arbitrary name in the user script). The single parameter is listed as table PROPS_GUI_COMPONENT, so it should get a table as argument. The name is chosen to refer to an item under Properties below. The return value is listed as being a component. This is a custom type defined by OctaneRender®.

The items under Properties are not present in the API, but they are descriptions of information that have to be sent to a function, or information that has to be returned from a function.

![](images/TheScriptMenuandLua5_489x419.jpg)

Figure 5: Properties items

 

A lot of functions in the Lua API Browser return a table. For example, using octane.gui.getProperties to get the properties of a GUI component returns a table containing information about the object that was just created. The contents of the table depends on the type of the component, but it is described by one of the items here. if you create a slider you will get a table with information described by the PROPS_GUI_SLIDER item. You can also find all the other component types here.

![](images/TheScriptMenuandLua6_492x394.jpg)

Figure 6: GUI component properties as a table

 

A lot of functions also take a single argument, which is a table. octane.gui.create is one example. For this function, these are the same descriptions as the ones returned from octane.gui.getProperties.

Pressing CTRL+F while in the LUA API browser brings up the Search dialog, which quickly finds and select nodes and dynamic pins that contain the search string.

![](images/TheScriptMenuandLua7_497x399.jpg)

Figure 7: Search dialog window
