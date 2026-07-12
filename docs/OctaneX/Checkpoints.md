The Checkpoint nodes are used to save a point in a compositing node tree that can be recalled further up the compositing stack. In figure 1, a checkpoint is saved before the Solid Color node. The checkpoint is then loaded after the Solid Color node, thus skipping the color overlay created by the Solid Color node. A Texture node is then applied and the checkpoint is discarded to save GPU memory once the checkpoint is no longer needed. 

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_543.png)       | Checkpoints                               |
|                                   |                                           |
|                                   | ![](images/Checkpoints_Fig01_SE_2024.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: A basic compositing node tree illustrating the usage of the Checkpoint nodes

### Checkpoint Nodes

#### Save Checkpoint

This node is used to save a snaphot of current composited results.  The Checkpoint Name is used to recall the saved checkpoint further up the compositing stack.

#### Load Checkpoint

This node is used to recall a previous snaphot of composited results. The Checkpoint Name is used to recall a specific saved checkpoint from a previous location in the compositing stack.

#### Discard Checkpoint

This node is used to purge a saved checkpoint.  Checkpoints are stored in GPU memory, this node helps to keep GPU memory usage more efficeint once a saved checkpoint location is no longer needed.
