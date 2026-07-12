You can manage OBJ Preferences by clicking on File \> Preferences \> Geometry Import \> OBJ. Vertex color support has been added which can sometimes be found in assets imported using the OBJ format. 

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_15.png)        | OBJ import                                            |
|                                   |                                                       |
|                                   | ![](images/OBJ_Import_Preferences_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: OBJ import preferences

### OBJ Import Preferences

Length Unit - Selects the unit of measurement used in the geometry. The default unit is in Meters.

Object Layers - Controls how OctaneRender® creates Object layer pins on the Mesh node to control the discrete objects.

Load Vertex Normals - Sets preferences related to geometry object smoothing, including the option to load the vertex normals supplied by the geometry file.

Maximum Smoothing Angle - This sets the smoothing angle for calculating normals. A value of 0 uses the normals in the OBJ file, and any value other than 0 uses that given smoothing angle set in OctaneRender to calculate normals for the imported Meshes. If OctaneRender has to calculate vertex normals, set the maximum smoothing angle to 89 so it does not smooth straight angles.

Merge Unwelded Vertices - Smoothing and rounded edges requires watertight closed polygons and edges shared between surfaces. This option closes polygons that are not watertight. Mesh optimization may not be appropriate in all cases, so this option is off by default.

#### Hair

Default Hair Thickness - This sets the value for the thickness of the polylines specific to hair primitives, which are stored in Mesh nodes to simulate hair render features.

Default Hair Gradient Interpolation - Specifies the basis for the data generated in applying color progression between colors in the gradient per strand of hair geometry. The interpolation could either be based on the hair length or on the segment count.

#### Particles

Default Sphere Radius - OctaneRender adapts the OBJ and Alembic standards for particles to import and export particle sizes. This parameter sets the size for particles imported if OctaneRender cannot locate the size or dimension data of the particles while importing the particle geometry.

#### Subdivide

Subdivision Level - Allows subdivision surface refinement based on Pixar's OpenSubDiv implementation. Controls the number of times OctaneRender subdivides the original version of the Mesh.

Subdivision Scheme - Select one of the OpenSubdiv subdivision scheme classes, which provides the methods for computing the various sets of weights used to compute new vertices resulting from subdivision.

- Catmull-Clark - A uniform refinement is applied to the Mesh faces. It subdivides the Mesh by the same amount.
- Catmull-Clark (Smooth Variant) - OpenSubdiv Catmull-Clark with a smoothed preview version of the Mesh.
- Loop - Subdivision scheme for triangular meshes, where each recursively defined subdivision surface divides into smaller ones.
- Bilinear - Subdivision scheme where the limit surface goes through the existing vertices, resulting in softened edges but no drastic changes in shape.

Subdivision Sharpness - Controls the Sharpness values for the crease at and around a vertex. Crease sharpness values range from 0 (smooth) to 10 (infinitely sharp).

File Sharpness Scale - Preserves the OpenSubdiv crease information exported from different 3D host applications. It is applied to the Vertex and Edge Crease values to get the desired sharpness on the model. Currently, Alembic and FBX file formats are able to export crease information.

#### Vertex Data

Boundary Interpolation -  Specifies the rule that controls how OctaneRender interpolates boundary edges and vertices.

- None - No boundary edge interpolation occurs. Instead, boundary faces are tagged as holes so that the boundary edge-chain continues to support the adjacent interior faces, but is not considered to be part of the refined surface.
- Edge Only - All the boundary edge-chains are sharp creases. Boundary vertices are not affected.
- Edge And Corner - All the boundary edge-chains are sharp creases, and boundary vertices with one incident face are sharp corners.

#### Face-Varying Data

Face-varying data like UVs and color sets are used when OctaneRender requires discontinuities in the data over the surface - often the seams between disjoint UV regions. Face-varying data can follow the same interpolation behavior as vertex data, or it can be constrained to interpolate linearly around selective features from corners, boundaries, or the entire Mesh interior.

Boundary Interpolation - Specifies the rule to control how OctaneRender interpolates face-varying data.

- None - Bilinear interpolation (no smoothing), or smooth everywhere the Mesh is smooth.
- Corners Only - Sharpens the corners by linear interpolation.
- Edge And Corners - Similar to the Corners Only option, but it does not infer the presence of corners where two face-varying edges meet at a single face.
- Boundaries - Linear interpolation occurs along all boundary edges and corners.
- All - Linear interpolation occurs everywhere in the boundaries and the interior.

Propagate Corners - Propagates corners in Edge and Corner mode.

#### OBJ

Polygon Winding Order - Determines how to control the Polygon normal input in the Mesh node. Set this parameter in a way that the polygon normals align with the vertex normal. This alleviates problems that occur when the polygon and vertex normals are pointing in the opposite directions, which happens with Specular materials and when applying displacement where the vertex or shading normals of displacement triangles are calculated during rendering using the polygon normals.

Import Smoothing Groups - Sets preferences related to material smoothing, including the option to load smooth groups supplied by the geometry file.

Import Materials From MTL files - Determines if OctaneRender imports any materials stored in an MTL file associated to the particular OBJ file.

Import Material Types - Specifies the material types to import.

Import Image Textures - Uses the Image textures as specified in the MTL file and lets you determine the data type of imported images, providing more flexibility during the setup prior to rendering.

Texture Types - Specifies the texture types to import.

Glossy Specular Scale - Adjusts the magnitude that OctaneRender interprets specular values in materials generated by third-party applications.

Invert Opacity Values - Added option to invert opacity values because some 3D applications write them inverted.

Invert Opacity Textures - Added option to invert opacity textures because some 3D applications write them inverted.

RGB Color - Choose between Linear or sRGB for the RGB colorspace.

+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                  |
|                                                                                                                                                                       |
| To have these changes take effect, you need to delete the Mesh node, change the settings in the Geometry Import \> Wavefront OBJ tab, and then import the Mesh again. |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
