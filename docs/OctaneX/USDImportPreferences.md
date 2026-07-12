You can manage USD import preferences by going to File \> Preferences \> Geometry Import \> USD.

+-----------------------------------+-------------------------------------------------------+
| ![](images/NewItem_19.png)        | USD import                                            |
|                                   |                                                       |
|                                   | ![](images/USD_Import_Preferences_Fig01_SE_v2026.jpg) |
+-----------------------------------+-------------------------------------------------------+

Figure 1: USD Import preferences

### USD Import Preferences

Length Unit - Tells OctaneRender® the unit of measurement used in the geometry. The default unit is in meters.

Object Layers - This controls how Object layer pins are created on the Mesh node to control the discrete objects.

#### Object Smoothing

Load Vertex Normals - Sets preferences related to geometry object smoothing including the option to load the vertex normals supplied by the geometry file.

Maximum Smoothing Angle - This sets the smoothing angle (degrees) for calculating normals. A value of 0 uses the normals in the OBJ file, and any value other than 0 uses that given smoothing angle set in OctaneRender to calculate normals for the imported meshes. In any case, if OctaneRender has to calculate vertex normals, set the maximum smoothing angle to 89 so it does not smooth straight angles.

Merge Unwelded Vertices - Smoothing and rounded edges requires watertight closed polygons and edges shared between surfaces. This option allows OctaneRender to close polygons that are not watertight. Mesh optimization may not be appropriate in all cases, so this option is off by default.

#### Hair

Default Hair Thickness - This sets the value for polyline thickness specific to hair primitives, which are stored in Mesh nodes to simulate hair render features.

Default Hair Gradient Interpolation - Specifies the basis for the data generated in applying color progression between colors in the gradient per strand of hair geometry. The interpolation could either be based on the hair length or on the segment count.

#### Particles

Default Sphere Radius - OctaneRender adapts the OBJ and Alembic standards for particles to import and export particle sizes. This parameter sets the size for particles imported if OctaneRender can not locate the size or dimension data of the particles upon importing the particle geometry.

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

#### USD

Load USD Materials - If enabled, USD preview surface materials are loaded from the USD file.

Override File Subdivision Level - Override all mesh subdivision levels with preference setting dialog\'s subdivision level.

Subdivide All Meshes - Subdivide all meshes in the geometry archive rather than the ones that were already loaded with subdivision settings from the imported file.
