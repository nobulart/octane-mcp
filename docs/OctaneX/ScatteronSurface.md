One of the features that makes Octane so powerful is the ability to handle a very large number of instances. Generating instances is usually done via third party tools which generate scatter data that can be imported into Octane.

Octane 2020.2 adds the node Scatter on Surface which generates an arbitrary number of instances according to various patterns and distributes them across a surface (figure 1). The node can be found under the Geometry category in the Nodegraph Editor window.

+-----------------------------------+---------------------------------------------------+
| ![](images/NewItem_54.png)        | scatter on surface                                |
|                                   |                                                   |
|                                   | ![](images/Scatter_On_Surface_Fig01_SE_v2021.jpg) |
+-----------------------------------+---------------------------------------------------+

Figure 1: The Scatter on Surface node and its associated parameters.

### Scatter on surface Parameters

#### Geometry

Surface - A geometry object can be specified here as the surface for scattering objects.

#### Objects

Scattered Object (1,2,3,4) - The objects to be scattered.

Object Selection Method - The method for scattering the connected objects. The available scattering methods are Sequential, Random, and Selection Map.

Object Selection Seed - Seed value used to randomize the selection of source objects.

Object Selection Map - The texture map used to associate each instance with a source object. This is only applicable when Selection Map is selected as the Object Selection Method.

#### Distribution

Distribution on Surfaces- The method used to distribute the instances on the scatter surface.

- - One Instance per Vertex: An instance is placed at each vertex.
  - One Instance per Edge: An instance is placed along the edges using the position and spacing values.
  - Evenly Spaced Instances on Edges: Instances are placed along edges but the results are more random than with the previous option.
  - One Instance per Polygon: Instances are placed at the center of each polygon.
  - Random Instances by Relative Area: Instances are placed randomly over the surface depending on the size of each polygon.
  - Random Instances by Relative Density:Instanced are placed randomly across the surface using a texture map specified in the Relative Density Map parameter.
  - Disabled: No instances are placed on the surface.

Distribution on Particles - This option will distribute the instanced on particles.

Distribution on Hair - Allows for instances to be distributed along hair strands

- - One Instance per Hair Vertex: An instance is placed at each vertex of each hair strand.
  - One Instance per Hair: Instances are placed on each hair strand using the specified position values.
  - Evenly Spaced Instances on Hair: Instances are placed along the hair strands using both the position and spacing values.
  - Disabled: No instances are placed on the hair strands.

Position on Edge - When scattering on edges, this defines the position of instances along the edge.

Spacing on Edges - When scattering on edges, this defines the spacing between instances along the edge.

Poisson Disk Sampling - When randomly scattering on the surface by area or relative density, this option distributes the instances so that no two instances are too close to each other.

Relative Density Map - The texture map used to control the relative density of the instances. This is only used when Distribution on Surfaces is set to Random Instances by Relative Density.

Position on Hair - When scattering on hair strands, this defines the position of the instances along the hair.

Spacing on Hair - When scattering on hair strands, this defines the spacing between instances.

Seed - The global seed used to randomize instance placement.

#### Density

Instances - When the Distribution Method is set to Surface Area or Relative Density, this parameter determines the total number of instances to scatter across the surface.

Culling Map - Texture map used to associate each instance with a value to control culling where instances in darker areas are more likely to be culled.

Culling Min - All instances in areas of the map that have a value below this threshold are removed.

Culling Max - All instances in areas of the map that have a value above this threshold are removed.

Culling Angle Low - All instances on surfaces with a normal below this threshold in relation to the reference up vector are removed.

Culling Angle High - All instances on surfaces with a normal above this threshold in relation to the reference up vector are removed.

#### Instance Orientation

Smooth Normals - Determines whether there should be smoothing applied across the surface of the instances.

Normal Align - Blend factor between the reference up direction and the default normal of the instance. Values closer to 0 align the instance with the reference up direction and values towards 1 align with the default normal.

Front Align - Blend factor between the reference front direction and the default front of the instance. Values towards 0 align the instance with the reference front direction, values towards 1 align with the default front. 

Orientation Priority - If the Up and Front Vector are not orthogonal, this parameter determines which one has priority.

Up Direction Mode - Selects between the use of a reference direction or a reference point. Reference point allows for finer (more localized) control over the orientation of the scatter objects.

Reference Up Direction - When Up mode is set to Direction, the reference up vector will point in this direction.

Reference Up Point - When Up mode is set to Point, the reference up vector will point towards this location.

Front Direction Mode - Selects between the use of a reference direction or a reference point for the front direction of the scattered objects.

Reference Front Direction - When Front mode is set to Direction, the reference front vector will point in this direction.

Reference Front Point - When Front mode is set to Point, the reference front vector will point towards this location.

#### Instance Transform

The parameters under this heading provide additional orientation controls that are added to the instance orientation specified in the previous category.

Rotation Mode - Determines how the rotation parameters will affect the instanced geometry.

Rotation Min - Specifies the minimum rotation value for the instances.

Rotation Max - Specifies the maximum rotation value for the instances.

Rotation Step - When the Rotation mode is set to Random or Map and this parameter is non-zero, the values will be aliased to the nearest step.

Rotation Map - The texture map used to associate each instance with a factor to control rotation.

Scale Mode - Determines how the scale parameters will affect the instanced geometry.

Scale Min - Specifies the minimum scale value for the instances.

Scale Max - Specifies the maximum scale value for the instances.

Scale Step - When the Scale mode is set to Random or Map and this parameter is non-zero, the values will be aliased to the nearest step.

Scale Map - The texture map used to associate each instance with a factor to control scale.

Translation Mode - Determines how the translation parameters will affect the instanced geometry.

Translation Min - Specifies the minimum translation value for the instances.

Translation Max - Specifies the maximum translation value for the instances.

Translation Step - When the Translation mode is set to Random or Map and this parameter is non-zero, the values will be aliased to the nearest step.

Translation Map - The texture map used to associate each instance with a factor to control translation.
