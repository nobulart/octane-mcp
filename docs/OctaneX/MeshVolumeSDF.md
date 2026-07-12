The Mesh Volume SDF node will import a 3D model in .obj format and convert it to a Signed Distance Field, SDF volume. The node can be found under the Geometry category in the Nodegraph Editor window. By default, the Mesh Volume SDF node has a [Diffuse](javascript:void(0);) material attached to it (figure 1). This can be changed to any other material type under the [Material](javascript:void(0);) rollout on the node. The node rebuilds a Signed Distance Field based on the Voxel Size and Border Thickness parameters available in the Import Settings (figure 2).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_40.png)        | mesh volume sdf                                |
|                                   |                                                |
|                                   | ![](images/Mesh_Volume_SDF_Fig01_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 1: The Mesh Volume SDF node used to convert an obj file to a signed distance field

The resolution or voxel size of the volume can be adjusted using the Edit Settings button (figure 2).

+-----------------------------------+------------------------------------------------+
| ![](images/NewItem_41.png)        | mesh volume sdf import                         |
|                                   |                                                |
|                                   | ![](images/Mesh_Volume_SDF_Fig02_SE_v2022.jpg) |
+-----------------------------------+------------------------------------------------+

Figure 2: Accessing the mesh volume import parameters from the Edit Settings button
