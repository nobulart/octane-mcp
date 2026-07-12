Settings related the user interface, default material previews, file locations, and file associations are managed in the Application tab of Preferences, which you can access by clicking on File \> Preferences \> Application. OctaneRender® uploads the saved settings to your online account, and the settings are available if you log into another copy of OctaneRender. More details pertaining to these options can be found in the Interface Layout section.

+-----------------------------------+--------------------------------------------------------+
| ![](images/NewItem_513.png)       | Application Tab                                        |
|                                   |                                                        |
|                                   | ![](images/Application_Preferences__Fig01_SE_2026.jpg) |
+-----------------------------------+--------------------------------------------------------+

Figure 1: Application tab

When saving projects, OctaneRender needs the specific location to store the project in a file system where these resources are represented by absolute or relative paths. An absolute, or full, path points to the same location in a file system, regardless of the current working directory. To do that, it includes the root directory. You can save projects using a relative path, which starts from some given working directory, thus avoiding the need to provide the full absolute path.

OctaneRender sends statistical data to a server to understand how OctaneRender is used, and it helps our development team make informed decisions for future developments. The statistics gathered are anonymous and independent of the OctaneRender LiveTM license server. The types of events sent in the statistical data include:

- SessionStart and SessionEnd events, which indicate one OctaneRender session.
- A Render event is sent if the rendering progresses more than 30 seconds or 1000 samples/pixel.

The events above are sent along with statistical information like the geometry size, kernel, GPU count, or Render Node count.

The statistics are important, but you can opt out and disable this facility by clicking on File \> Preferences... \> Application \> Enable statistics.
