You can manage settings related to the user interface, default material previews, file locations, and file associations in the Applications Settings dialog box. To open the Application Settings, click File \> Application \> Preferences.

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_9.png)         | Application settings                                |
|                                   |                                                     |
|                                   | ![](images/Application_Settings_Fig01_SE_v2026.jpg) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: Application settings

When saving projects, OctaneRender® needs the specific location to store the project in a file system, where these resources are represented by absolute or relative paths. An absolute or full path points to the same location in a file system, regardless of the current working directory. To do that, it includes the root directory. You can save projects using a relative path, which starts from some given working directory, and avoid the need to provide the full absolute path.

### Notable Application Settings Preferences

Developer Options - If you are developing Lua and OSL scripts for use with OctaneRender, you can enable this section and specify paths to the OSL to include directories here so that OctaneRender can locate the included files at compile time. There should be one path per line. If a path begins with a tilde (\`), the tilde expands to your home directory.

Statistics - OctaneRender sends statistical data to a server to understand how OctaneRender is used, which helps our development team make informed decisions for future developments. The statistics gathered are anonymous and independent of the OctaneRender LiveTM license server. These are the types of events sent in the statistical data:

- SessionStart and SessionEnd events, which indicate one OctaneRender session.
- Render events are sent if the rendering progresses more than 30 seconds or 1000 samples/pixel.

In addition to these events, statistical information like the geometry size, kernel, GPU count, and Render Node count is sent as well. The statistics are important, but you can opt out and disable this feature by clicking File \> Preferences... \> Application \> Enable Statistics.

Max Cores - This refers to the number of cores used to train OctaneRender. By default, the limit is off, and all threads are used. However, you can enable a limit up to 8 threads for the AI scene.

File Caching - This limits the disk space used for caching textures.

File Associations - Establishes the relationship between the specified file types to OctaneRender. It registers and defines OctaneRender as the default program to open files with these file extensions.
