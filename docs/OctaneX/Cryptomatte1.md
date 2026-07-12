Cryptomattes are a render-time image matte generation system for use with image compositing applications. Cryptomattes create multi-colored ID mattes with support for motion blur, transparency, and depth of field, with no additional render time penalty. These mattes, or ID channels as Cryptomatte refers to them, are typically derived from material names, object names, instance IDs and other attributes. Cryptomatte can be a tremendous time saver, especially for complex scenes, as it allows work is focused on shot design and creation as opposed to technical matte generation for compositing.

### HOw Cryptomattes Work

Cryptomattes use an ID-coverage paring technique, where one channel represents an area of the image for a given channel, and the other channel represents the coverage of that channel in the image. The ID channel is one object per pixel. The coverage channel determines how much of the pixel is contributed to by the assigned object. These ID-coverage pairs are then ranked to add support for multiple objects per pixel (the ranking determines layer priority of object 1 to object n, front to back). That is why the Cryptomatte channels are always in pairs of two. Keep in mind that Cryptomattes are typically 32 bits per pixel, which adds to resource consumption. When loading EXR files that contain cryptomattes into compositing software with a cryptomatte decoder, it is merely a matter of choosing the different matte ID channels needed to compose elements. 

#### Cryptomatte ID Channels

Material Node - The Cryptomatte channel is based on distinct material nodes. 

Material Node Name - The Material Node Name channel is used to create IDs by assigned materials in the scene. Using the same material on different objects will result in those objects having the same color (ID channel) in the cryptomatte output.

Material Pin Name - The channel ID is used to get polygon/material selections in the scene. Selections will be one channel, and null selections (nothing selected) will be in another channel.

Object Node - The Cryptomatte channel is based on distinct Object nodes. 

Object Node Name - The Object Node Name channel is used to create ID Channels based on object names for each object in the scene.

Object Pin Name - The ID channel is based upon the names of the exiting Object pins in the scene. It is quite common to see most objects placed into the same ID channel, as Object Node Pin Names change, rarely, depending upon the object source.

Object Pin Name - The Cryptomatte channel is based on the names of the existing Object pins in the scene. 

Instance - The ID channel is based on instance IDs.

Geometry Node Name - The ID channels are generated based upon the name of the scene geometry.

Render Layer - The ID channels are generated based upon the Render Layer ID in the Octane Layer node connected to objects in the scene. 

User Instance ID - The ID channels are generated as determined by the Instance IDs specified by the user.
