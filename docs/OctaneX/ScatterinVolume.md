One of the features that makes Octane so powerful is the ability to handle a very large number of instances. Generating instances is usually done via third party tools which generate scatter data that can be imported into Octane.

Octane 2020.2 added the node Scatter in volume which generates an arbitrary number of instances according to various patterns and distributes them in a volume (figure 1). The node can be found under the Geometry category in the Nodegraph Editor window.

+-----------------------------------+----------------------------------------------------+
| ![](images/NewItem_53.png)        | scatter in volume                                  |
|                                   |                                                    |
|                                   | ![](images/Scatter_in_Volume_Fig01_SE_v2020_2.jpg) |
+-----------------------------------+----------------------------------------------------+

Figure 1: The Scatter in Volume node and its associated parameters.

 

### Scatter in Volume Parameters

 

#### Objects

Scattered Object (1,2,3,4) - The objects to be scattered.

Object Selection Method - The method for scattering the connected objects. The available scattering methods are Sequential, Random, and Selection Map.

Object Selection Seed - Seed value used to randomize the selection of source objects.

Object Selection Map - The texture map used to associate each instance with a source object. This is only applicable when Selection Map is selected as the Object Selection Method.

 

#### Grid

Dimension - Determines the number of instances along each dimension (x,y,z).

Offsets - Determines the offset between the instances along each dimension (x,y,z).

 

#### Shape

Shape - Determines the shape of the volume in which the objects are scattered.

Culling Map - Texture map used to associate each instance with a value to control culling.

Culling Min - All instances in areas of the map that have a value below this threshold are removed.

Culling Max - All instances in areas of the map that have a value above this threshold are removed.

 

#### Instance Orientation

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
