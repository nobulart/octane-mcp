OSL defines strings as inputs and outputs of various functions:

- - Noise types supported by the noise() function: \"uperlin\", \"perlin\", \"noise\", \"snoise\", \"cell\", \"circular\", \"chips\", \"voronoi\", \"scircular\", \"schips\", \"svoronoi\".
  - Ray types supported by raytype(): \"camera\", \"shadow\", \"diffuse\", \"glossy\", \"reflection\", \"specular\", \"refraction\", \"AO\".
  - Keys supported by getattribute(): \"camera:resolution\", \"camera:pixelaspect\", \"camera:projection\", \"camera:[fov](javascript:void(0);)\", \"camera:clip_near\", \"camera:clip_far\", \"camera:clip\", \"camera:distortion\", \"hit:obj-seed\", \"hit:w\", \"hit:local-shader-dir\", \"pixel:pos\".
  - Keys supported by gettetureinfo(): \"exists\", \"resolution\", \"channels\",
  - Values supported for the wrap option for texture() calls: \"black\", \"white\", \"clamp\", \"mirror\", \"periodic\".
  - Values returned by getattribute(\"camera:projection\"): \"spherical\", \"cylindrical\", \"cube\", \"cube:+x\", \"cube:-x\", \"cube:+y\", \"cube:-y\", \"cube:+z\", \"cube:-z\", \"perspective\", \"orthographic\", \"baking\".

For more string constants and learning more about programming with the [Open Shader Language](javascript:void(0);), see [The Octane OSL Guide](https://docs.otoy.com/osl/index.md).
