OctaneRender® supports participating media inside objects. These settings are stored in Medium nodes, which are attached to the corresponding input pin of [Diffuse](javascript:void(0);), [Specular](javascript:void(0);), Null, and Universal material nodes.

There are seven types of nodes available for medium creation. Additionally, there are numerous Switch nodes that can be used to connect multple medium nodes to one input.

- - [Scattering](javascript:void(0);) - Has parameters for [Absorption](javascript:void(0);), Scattering, and Emission.
  - Random Walk - A newer variant of subsurface scattering that ensures a more realistic result.
  - Absorption - A simple version with just Absorption parameters.
  - Schlick Phase Function - An independent node that can be used to control which direction the scattering occurs.
  - Standard [Volume Medium](javascript:void(0);) - A comprehensive node with the flexibility to specify what [VDB](javascript:void(0);) grid data can be used for the various node channels.
  - Volume Medium & Gradient - See the [Effects](Effects.md) section for more details.

To render with Medium nodes, the Path Tracing or PMC render kernels are the best choices. You can render mediums using the Direct Light kernel, but only if the Medium node is connected to a Diffuse material, and if you set the kernel\'s Diffuse Mode to GI.

To add a Medium node to a scene, right-click anywhere in the Nodegraph Editor and select Medium from the context menu (Figure 1). Choose the type of node you want to use. You should connect Absorption and Scattering mediums to the Medium input of the Diffuse or Specular material. Volume mediums can connect to VDB file inputs. Schlick Phase Function and Volume Gradient are special nodes that modify the other Medium nodes.

+-----------------------------------+----------------------------------------+
| ![](images/NewItem_402.png)       | mediums                                |
|                                   |                                        |
|                                   | ![](images/Mediums_Fig01_SE_v2023.jpg) |
+-----------------------------------+----------------------------------------+

Figure 1: Selecting a Medium node from the Nodegraph Editor

There are some things to keep in mind about using [Mediums](javascript:void(0);) with meshes and specular materials:

### Meshes

Add Medium nodes to m[aterials](javascript:void(0);) when you\'ve applied them to meshes that define a closed volume. A single-sided plane will not work. For example, a plane representing a leaf will not work if a m[aterial](javascript:void(0);) with a medium is applied to it. The one exception is a plane representing the ground: OctaneRender treats the ground plane as an infinitely deep surface.

 

### Specular and Null Materials

Specular materials were the best choice when using a medium node. When using a [Specular](javascript:void(0);) [](javascript:void(0);) [material](javascript:void(0);), set the value of the Reflection parameter to a low value because only the part of the spectrum that is not reflected can enter the object for scattering. If you set Reflection to 1, all light reflects regardless of the [Transmission](javascript:void(0);) value. If Reflection is set to 0, all light transmits through the surface, but the result is an unnatural appearance. Reflection values of 0.1 - 0.2 are good starting points.

However, the Null Material node can now be used for mesh objects that have an invisible surface but contain a medium. This is equivalent to setting up a specular material with IOR 1 and a reflection of 0 and a transmission of 1. However, that methodology no longer makes sense with nested dielectric. The Null Material was created to make a medium with no surface work in all cases.
