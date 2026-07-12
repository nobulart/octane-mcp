The [Diffuse](javascript:void(0);) material is used for dull, non-reflecting materials or light-emitting surfaces (figure 1). [Diffuse material](javascript:void(0);) simulates a rough surface that reflects light back into the environment in all directions. [Specular](javascript:void(0);) highlights and reflections do not appear on diffuse surfaces.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_88.png)        | Diffuse MAterial                                |
|                                   |                                                 |
|                                   | ![](images/Diffuse_Material_Fig01_SE_v2024.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: The OctaneRender® Diffuse material

### Diffuse Material Parameters

Diffuse- Provides color to the material. This is also known as base color or albedo. You can set Diffuse color by using a value, or connecting a Procedural or Image texture.

[Transmission](javascript:void(0);)- Uses a color or texture that is mixed with the material's Diffuse color, and is most noticeable in areas affected by indirect lighting.

BRDF Model - Provides three models for diffuse light reflectance. Lambertian reflects light equally in all directions and does not support roughness. The Octane option creates a sheen effect much like velvet. And, the Oren-Nayar option behaves more like clay.

Roughness - Determines the spread of highlights on the surface. A high Roughness value or light color can simulate very rough surfaces such as sand paper or clay. You can set Roughness using a value, or by connecting a Procedural or Image texture. A roughness value of 1 (white color) creates a diffuse sheen along the edges of the surface, simulating the look of crushed velvet.

Medium- OctaneRender® has three types of mediums to create translucent surfaces:

- [Absorption](javascript:void(0);) Medium - Produces the appearance of a material that absorbs light while passing through a surface. The resulting color depends on the distance that light travels through the material. For more information, see the Texture Overview topic in this manual.
- Random Walk - A newer variant of subsurface scattering that utilizes a stochastic or random process for the scattering of light through an object. This provides the most realistic result when rendering scatter volumes.
- [Scattering](javascript:void(0);) Medium - Similar to the Absorption medium, but with an additional option for simulating subsurface scattering. Subsurface scattering is the phenomena that gives human skin and similar organic surfaces their characteristic glow under certain lighting conditions. It\'s a major component for creating the look of realistic skin. For more information, see the Texture Overview topic in this manual.
- Standard Volume - This provides volume medium options with comprehensive controls for adjusting volume, scatter, transparency, emission, and temperature parameters based on imported VBD grid data.
- [Volume Medium](javascript:void(0);) - Adds color and other qualities to a [VDB](javascript:void(0);) file. VDBs are a generic volume format for creating effects such as smoke, fog, vapor, and similar gaseous objects. VDBs can consist of a single frame, or an animated sequence. 3D software packages like Houdini generate and export VDBs. You can also download VDB files at [](http://www.openvdb.org/download/) <http://www.openvdb.org/download/>.

Opacity - Determines what parts of the surface are visible in the render. Dark values indicate transparent areas, and light values indicate opaque areas. Values in-between light and dark indicate semi-transparent areas. You can lower the Opacity value to fade the object\'s overall visibility, or you can use a Texture map to vary the opacity across the surface. For example, if you want to make a simple polygon plane look like a leaf, you would connect a black-and-white image of the leaf's silhouette to the Opacity channel of the Diffuse shader. When using an Image texture map, set the Data Type to Alpha Image if the image has an alpha channel, or Grayscale Image for black-and-white images, to load an image for setting the transparency. To invert the transparency regions, use the image\'s Invert checkbox.

Bump - Creates fine details on the material's surface using a Procedural or Image texture. Often a Greyscale image texture connects to this parameter - light areas of the texture indicate protruding bumps, and dark areas indicate indentation. You can adjust the Bump map\'s strength by adjusting the Power or [Gamma](javascript:void(0);) values on the Image texture node. These attributes are covered in more detail in the [Texture](Textures.md) topic in this manual.

Bump Height - Determines the height represented by a normalized value of 1.0 in the bump texture. A vaule of 0 disables the bump map and a negative value will invert the bump map. 

Normal - Creates the look of fine detail on the surface. A Normal map is a special type of Image texture that uses red, green, and blue color values to perturb the surface normals at render time, giving the appearance of added detail. They can be more accurate than Bump maps, but require specific software such as ZBrush®, Mudbox®, Substance Designer, xNormal, or others to generate. To load a full-color Normal map, set the Normal channel to the RGB Image data type. Note that Normal maps take precedence over Bump maps, so you cannot use a Normal map and a Bump map at the same time.

[Displacement](javascript:void(0);) - Adjusts the height of a surface\'s vertices at render time using a texture map. Displacement maps differ from Bump or Normal maps in that the geometry is altered by the texture, as opposed to just creating the appearance of detail. Displacement mapping is more complex than using a Bump or Normal map, but the results are more realistic, especially along a surface\'s silhouette. Displacement only works with the Texture Image node, and the displaced mesh must have UV Texture coordinates. Other Texture nodes, such as Turbulence or Marble, will not work with Displacement. For more information, see the [Displacement](Displacement.md) topic in this manual.

Smooth - Smooths out the transition between surface normals by blending the polygon edges together. If this option is disabled, the edges between the polygons of the surface appear sharp, giving the surface a faceted look.

Smooth Shadow Terminator - If enabled, self-intersecting shadows are smoothed according to the polygon\'s curvature.

Round Edges - Rounds the geometry edges by using a shading effect instead of creating additional geometry. See the [Round Edges](RoundEdges.md) topic in this manual for more information.

Priority - Used to resolve the ambiguity in overlapping surfaces, the surface priority control allows artists to control the order of preference for surfaces. A higher number suggests a higher priority for the surface material, which means it is preferred over a lower priority surface material if a ray enters a higher priority surface and then intersects a lower priority surface while inside the higher priority surface medium.

Emission - Also known as a Mesh emitter, this creates a surface that emits light. To activate an emission, connect the Emission input of the Diffuse material to either a Blackbody or a Texture emission map. The [Textures](Textures.md) and the [Mesh Emitters](MeshEmitters.md) (under Lighting Overview) topics in this manual cover maps in more detail.

[Shadow Catcher](javascript:void(0);) - Converts the material into a Shadow Catcher, which is visible in areas that are in shadows. All other areas are transparent in the render.

Custom AOV - Writes a mask to the specified custom AOV.

Custom AOV Channel - Determines whether the custom AOV is written to a specific color channel (R, G, or B) or to all the color channels.

[Material](javascript:void(0);) Layer - Adds a Material Layer above the base material. See the [Material Layers](MaterialLayers.md) topic in this manual for more details.
