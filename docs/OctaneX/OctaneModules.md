Modules are separate [GPU](javascript:void(0);) rendering extensions that add new functionality to OctaneRender®. These are dependent on the services provided by the Standalone edition and are created by third-party developer clients through OctaneRender's Module API for the purpose of integrating in the Standalone edition. The term modules helps avoid confusion with the term plugin, which is already used for integrations of OctaneRender® in other 3D modeling host applications.

With the module API, the following files are provided:

- - Most up-to-date version of this document.
  - API header files. All their names start with api (e.g. apiprojectmanager.h).
  - API wrapper header and source files. All their names start with octanewrap (e.g., octanewrapprojectmanager.h).
  - octane.lib is provided for linking on Windows®.
  - Example modules directory.

### Loading Modules

Modules are loaded once upon startup. Once OctaneRender® is running, it\'s not possible to unload modules already loaded or load new modules. OctaneRender® searches recursively for shared libraries in the modules directory. The libraries are recognized by their file extension (.so for Linux, .dll for Windows®, and .dylib for macOS®). You can configure the modules directory can be configured via the preferences dialog. You can skip loading modules by using the \--no-modules command line option. When OctaneRender® seems to hang at startup, it could be that it crashed because of your module code. You can skip module loading to verify this.

You can get more info about the module loading by enabling the moduleLoader log flag. To enable this log flag (and other log flags), create a file named octane_log_flags.txt in the directory of the Octane binary. This file should have each log flag on a new line. To print out all the log flags, add logFlags to this file.

 

### Writing Modules

Modules are written in C++. Each module needs a start and stop function. The start function is called once when OctaneRender® loads from the command line. The stop function is called once before OctaneRender® quits. These functions are the entry points for OctaneRender® into your code. It\'s important that these functions have the correct name and signature, and that their symbol is visible in your module library. You should define these functions as extern C to avoid name-mangling. The easiest is to use the macros defined in apimodule.h. In the start function, the module should register itself with OctaneRender®. One library (module) is allowed to implement multiple modules, so register can be called multiple times in the start function. Registration is done from within the start function.

The API is made up of all the header files that start with api. This API is C++, but with some limitations to avoid problems that can occur at dll boundaries. Because of this, the API isn\'t always easy and intuitive to use - that is why we provided C++ convenience wrappers around most of the API code. If the code is trivial, we don\'t provide wrappers. All the wrappers are in the files prefixed with octanewrap. We recommend using the wrappers because it makes life a lot easier. The wrappers should be compiled as part of the module code. For convenience, we provide octanemoduleapi.h\` and \`octanemoduleapi.cpp so that you have to include/compile only a single file.

We try our best to provide good documentation for the API in the header files. If you run into problems, the forum is the best place to ask for help.

### Module IDs

Each module is identified by a unique ID. Once an ID is assigned to a module, it cannot be re-used for a different module. For help, visit our help page at https://help.otoy.com/hc/en-us.

#### Module Types

There are different types of modules, and each type integrates differently in OctaneRender®:

Command Module - Modules of this type execute a command. Executing a command is very generic and can be everything from saving a file, opening a window, and so on. Each command module gets a menu entry in the Modules menu. When you click on the menu entry, OctaneRender® calls the command\'s execute function. Commands are the most flexible plugins in OctaneRender®.

Work Pane Module - Work pane modules implement a GUI component that can dock into the OctaneRender® workspace. Work pane modules have a menu entry in the Window menu, and when launched, they are created in a separate undocked window. There can be only a single instance of a work pane module. Work pane modules are destroyed when you load a new project. You can save the work pane module as part of your default layout.

 

### Threading

The main thread running in OctaneRender® is called the message thread. This is the thread that runs OctaneRender® itself, and most of the code is executed by the message thread (user interface, node system evaluation, etc.). OctaneRender® always calls your plugin from the main thread unless documented otherwise. You can only call the API from the main thread, except for a few specific classes. This is documented at the top of those classes (e.g., ApiRenderEngine, ApiLogManager, etc.).

A good practice is to use the macro OCTANE_API_ASSERT_MESSAGE_THREAD defined in octanewrapthread.h to make sure that you aren\'t calling the API from the wrong thread.

### Compilation

If you are using the wrappers, they should be compiled with your module code. If you use Windows®, your module code needs to link against octane.lib. If you use macOS®, you need to specify -undefined dynamic_lookup to the linker options.

The compilers we tested with are Visual Studio 2010 (Windows you need to specify -undefined dynamic_lookup to the linker options.), g++-4.8.4 (Linux) and Clang 6.10 (macOS).

### Examples

The easiest way to get started with the API is by studying the example modules. You can build the examples on Windows® with the Visual Studio solution octane-modules.sln. For Linux and macOS®, CMake files are provided for each example module. You can build all modules by executing the script build-modules.sh The examples we provide are:

Hello World Module - Shows how to register a module, use the log manager, and create a window.

Work Pane Module - Shows how to create a work pane module, and demonstrates how to create various user interface components.

Texture Commander Module - Shows how to use the table component, and how to correctly interact with the node system and events generated by the node system.

 

### Warnings

Some warnings and potential pitfalls:

- - Your code is not running in a sandbox. A crash in your code will crash OctaneRender®.
  - Keep an eye on the log output. Errors generated by your module will display here.
