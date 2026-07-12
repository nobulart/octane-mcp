The OSL Projection node is a scriptable node where you write OSL ([Open Shader Language](javascript:void(0);)) scripts to define arbitrary projection types. It\'s similar to an OSL Texture node, but it connects to a Projection input. OSL is a standard created by Sony Imageworks. To learn about the generic OSL standard, information is provided from the [OSL Readme](https://github.com/imageworks/OpenShadingLanguage/blob/master/README.md) and [PDF documentation](https://app.readthedocs.org/projects/open-shading-language/downloads/pdf/latest/).

+-----------------------------------+-----------------------------------------------------+
| ![](images/NewItem_298.png)       | OSL Projection                                      |
|                                   |                                                     |
|                                   | ![](images/Oslprojection_nodeconnect_SEv3-08-4.png) |
+-----------------------------------+-----------------------------------------------------+

Figure 1: An OSL Projection node is connected to the projection input pin of an Image texture node

The customized OSL script is written into the OSL Projection node to create custom camera types. To edit the script, click on the pencil icon to go to the script editor window. If the script exists as an external OSL file, click on the Load icon and insert the OSL file into the node. Any existing file already used within an OSL camera node may be edited. To refresh the file and use the edits, click on the Reload icon.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_669.png)       | OSL Projection                                  |
|                                   |                                                 |
|                                   | ![](images/Oslprojection_inspector_v3-08-4.png) |
+-----------------------------------+-------------------------------------------------+

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_670.png)       | OSL Projection                                     |
|                                   |                                                    |
|                                   | ![](images/Oslprojection_scriptarea_SEv3-08-4.png) |
+-----------------------------------+----------------------------------------------------+

Figure 2: The script editor window showing the initial script of the OSL Projection node

When you invoke an OSL Projection node in OctaneRender's node system, the node is provided with an initial OSL script (Figure 3):

Shader OslProjection (

output point uvw = 0)

{

uvw = point(u, v, 0);

}

The initial script's declaration component includes one required output variable with output type point. The OSL I/O type "point" corresponds to an OctaneRender® projection attribute node (Box, Mesh UV, Spherical, Cylindrical, etc.).

A projection shader must have one output of a point-like type. All global variables have the same meaning as within texture shaders. The output value specifies a texture coordinate.

For a list of OSL variable declaration Input/Output types in the OSL Specification that OctaneRender® supports, refer to the Appendix topic on OSL Implementation in this manual. To learn more about scripting within OctaneRender® using the Open Shader Language, refer to [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).
