The Effects - Display category of Output AOVs contains numerous nodes for converting composites to different dsiplay types. 

### Covert Nodes

#### Convert for SDR Display (ACES)

Enabled - Determines whether this node is displayed or not.

#### Convert for SDR Display (AgX)

Enabled - Determines whether this node is displayed or not.

Punchy - Determines whether to apply the punchy look. 

#### Convert for SDR Display (Basic)

Enabled - Determines whether this node is displayed or not.

Highlight Compression - Reduces burned out highlights by compressing them and reducing their contrast. 

Clip to White - Controls the extent to which clipping is done per channel.

#### Convert for SDR Display (OCIO)

Enabled - Determines whether this node is displayed or not.

View - The OCIO view that produces the sRGB output. 

Look - The OCIO look to apply, if the OCIO configuration file loaded in the Preferences window contains looks

#### Convert for SDR Display (Smooth)

Enabled - Determines whether this node is displayed or not.

Highlight Rolloff - Determines how smoothly to compress highlights to prevent clipping. 0.0 produces hard clipping (no rolloff). Values larger than 1.0 will start to ntocieably darken midtones.

Desaturate Highlights - If enabled, saturation of bright colors will be sacrificed to preserve more luminance information. If disabled, saturation will always be preserved at the expense of luminance.

Saturation Rolloff - Determines how smoothly to transition from increased input  luminance causing increased output luminance to increased input luminance causing decreased output saturation. 

#### Dither for 8-bit Display (SDR Only)

Enabled - Determines whether this node is displayed or not.
