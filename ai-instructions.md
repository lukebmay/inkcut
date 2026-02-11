This is Inkcut (project: <https://github.com/inkcut/inkcut>), a plugin for Inkscape that facilitates sending vector designs to vinyl cutters.It is written in Python and uses an declarative UI library called enaml that is built on top of Qt. It is designed to be multi-platform (Linux, Windows, Mac).

Keep code clean, try not to repeat code too often, use good human readable names that are concise as possible while clearly describing the data or action associated with the name.

This code base did not start with typings. Please add types to files as you go where you are able.

Code Structure overview:

`inkcut/device` - UI and models for the device specific options
`inkcut/job` - UI and models for the design to be cut (or the current job)
`inkcut/preview` - UI and models for the preview of the design (before cut, not the live preview done during the cut)
