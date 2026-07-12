The Joint node is available as a tool to control skeletal systems that can be imported into Standalone using the [FBX](javascript:void(0);) format. The node can be found under the Geometry category in the Nodegraph Editor window. It is not meant to be used as a standalone node, only as a node auto-generated when a skeletal mesh system is imported. The Joint node controls joints and can be used to control skeletal animations. Note that the Joint node only supports FK animation.

### Support For FBX And glTF

OctaneRender® supports loading FBX and glTF files. Both file formats load as a geometry archive, i.e. a Node Graph with lots of stuff inside and providing material and object layer input linkers as well as camera and geometry output linkers.

Although OctaneRender® supports bones, it does not support inverse kinematic (IK) animations. This means it is necessary to convert any IK animation to forward kinematic (FK) to make the FBX files work in OctaneRender®.

### Support For Bone Deformations

To support FBX and glTF, OctaneRender® has support for bone deformations. Character animations can be more lightweight than if the deformed geometry needs to be baked, as in the case with [Alembic](javascript:void(0);).

Bone deformations are set up in the respective source 3D modeling applications, and are not editable from the Nodegraph Editor. At this stage, the Bone Deformation node and the Joint node exists for the benefit of the FBX and gITF files, and potential optimizations in the geometry compilation.
