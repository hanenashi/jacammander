# Jacammander

Jacammander is a small modular Python LAN file transfer and remote file management tool aimed at dead-simple use between Windows machines, including awkward combinations such as Windows XP, Windows 8.1, and Windows 11.

The original trigger was a very practical one: copying files from an older machine to a newer one without having to wrestle with SMB, network discovery, permissions hell, or the usual Windows networking nonsense. A tiny HTTP server would already solve one-way transfer, but Jacammander aims for the more useful middle ground: a purpose-built, simple GUI app with proper folder browsing and basic file operations.

The intended spirit is:
- dead simple GUI
- modular codebase
- Python-first development
- easy packaging to EXE
- English-first development, localization later
- useful logs and debug output
- local-network use only

## TL;DR

Jacammander is planned as a single codebase Python app with two modes:
- Server mode
- Client mode

Primary purpose:
- browse files on a remote machine over LAN
- copy files both ways
- later support move, delete, rename, and folder creation

The main design goal is to fill the annoying gap between:
- browser-based quick transfer tools that are too limited
- existing heavy tools such as FTP/SFTP clients that are powerful but annoying to set up for casual users

PuTTY is not the right tool for this. WinSCP and FileZilla are in the right general area, but they require extra infrastructure or setup and are not tailored to the intended simple workflow.

## Why build this when software already exists?

Because the existing choices split into two annoying camps:

1. Quick-send tools
- easy
- low setup
- usually no folder browsing or proper remote file management

2. Full file transfer clients
- powerful
- usually require SSH/FTP/SFTP setup
- more UI and setup burden than needed for a simple home LAN workflow

Jacammander aims for the sweet spot:
- simple GUI
- no unnecessary protocol baggage in the first version
- remote folder browsing
- copy both ways
- later basic file operations
- one-purpose tool with minimal user friction

## Early platform reality

The project was discussed with Windows XP and Windows 11 as a possible first test pair.

This matters because XP compatibility strongly influences technical choices.

### XP implications

If XP support is desired, the code should be kept compatible with an older Python line, realistically in the Python 3.4 era.

That means avoiding newer language and library conveniences, such as:
- f-strings
- pathlib-heavy code
- type hints
- modern third-party GUI stacks

XP also suggests using a very conservative GUI stack:
- Tkinter
- simple widgets
- minimal dependencies

This is not because XP is impossible. It is because XP is old, touchy, and best approached without heroic modern UI ambitions.

## Technical direction

### High-level architecture

The app should be modular from the start.

Planned layers:

1. Core
- file operations
- path validation
- safe root-folder enforcement
- command definitions
- transfer logic
- security helpers

2. Networking
- sockets
- listener/client connection handling
- packet send/receive
- JSON-based message exchange
- threaded communication

3. GUI
- Tkinter windows and widgets
- client/server panels or startup mode selection
- file views
- buttons and dialogs
- progress/status display

4. Config
- JSON settings load/save
- defaults
- remembered paths and connection info
- language selection later
- debug toggles

5. Debug
- console logging
- optional file logging
- exception capture
- shared logger usable by GUI and non-GUI code

### Recommended single-codebase strategy

One codebase, two modes.

Possible runtime modes:
- Server
- Client

Recommended early behavior:
- one entry point
- startup chooser to select mode

This keeps the codebase unified while avoiding the pain of maintaining separate apps too early.

## Proposed repository structure

jacammander/
|
|- main.py
|- launcher.py
|- requirements.txt
|- README.md
|
|- app/
|  |- __init__.py
|  |
|  |- core/
|  |  |- __init__.py
|  |  |- protocol.py
|  |  |- file_ops.py
|  |  |- transfer.py
|  |  |- security.py
|  |  \- validators.py
|  |
|  |- net/
|  |  |- __init__.py
|  |  |- server.py
|  |  |- client.py
|  |  |- connection.py
|  |  \- packet.py
|  |
|  |- gui/
|  |  |- __init__.py
|  |  |- app_window.py
|  |  |- server_panel.py
|  |  |- client_panel.py
|  |  |- dialogs.py
|  |  \- widgets.py
|  |
|  |- config/
|  |  |- __init__.py
|  |  |- settings.py
|  |  \- defaults.py
|  |
|  |- debug/
|  |  |- __init__.py
|  |  |- logger.py
|  |  \- crash_handler.py
|  |
|  \- common/
|     |- __init__.py
|     |- constants.py
|     \- utils.py
|
|- assets/
|  \- icon.ico
|
\- build/
   \- pyinstaller.spec

This is modular enough to stay sane, but not so over-engineered that a tiny LAN utility turns into fake enterprise theater.

## GUI direction

The GUI should stay intentionally simple.

### Server window
Planned contents:
- shared folder selection
- port field
- password field
- start server button
- stop server button
- connection status
- log box

### Client window
Planned contents:
- server IP
- port
- password
- connect/disconnect
- local path
- remote path
- local file list
- remote file list
- action buttons such as Copy, Refresh, Up
- log/status area

Client GUI should remain the richer side. Server GUI should be lean.

## Protocol direction

No web browser transport as the main architecture.
Use a custom LAN protocol over Python sockets.

Suggested command family for early protocol design:
- AUTH
- LIST
- DOWNLOAD
- UPLOAD
- DELETE
- MOVE
- MKDIR
- RENAME
- PING

Recommended message style:
- JSON for control messages / metadata
- chunked binary transfer for file contents

This gives enough structure without dragging in FTP/SFTP complexity in v0.1.

## Safety rules

Very important design constraints discussed early:
- server should expose only one chosen root folder
- all file operations must stay inside that root
- no path escape via ..
- local LAN only
- simple password or shared key in early versions
- optional read-only mode is desirable later

The point is not military security theater. The point is to avoid obvious foot-shooting.

## Settings direction

Use a simple JSON settings file.

Example shape:

{
  "mode": "client",
  "server_port": 9009,
  "server_root": "C:/JACANA_SHARE",
  "last_server_ip": "192.168.1.15",
  "remember_password": false,
  "window_width": 980,
  "window_height": 640,
  "language": "en",
  "debug_enabled": true
}

Keep it flat at first.
No need to build a cathedral for a shed.

## Logging and debug strategy

The project should keep a visible debug/console layer from the start.

Desired behavior:
- development runs can show console output
- GUI can display log output from the same logger
- optional log-to-file support later
- log levels such as INFO, WARN, ERROR, DEBUG

Examples of preferred logging style:
- INFO Connected to 192.168.1.20:9009
- INFO Listed 42 items in /Photos
- WARN Refused path outside shared root
- ERROR Transfer failed: connection lost

Readable logs matter. Ancient networking problems rarely introduce themselves politely.

## Localization later

Development language should be English first.
Localization should be added later.

To avoid pain later, visible UI strings should be centralized early instead of hardcoded everywhere.

Possible later direction:
- strings_en.py or en.json
- strings_cs.py or cs.json
- maybe ja.json

But for now:
- develop in English only
- keep text centralized where reasonable

## Packaging direction

Packaging should stay easy.

To support that:
- keep dependencies minimal
- prefer standard library in v0.1
- Tkinter for GUI
- one main entry point
- avoid weird dynamic import patterns

PyInstaller is the obvious first packaging route.

XP may require older build tooling later. That is an implementation detail to manage when needed, not a reason to make the code messy now.

## Scope guidance

Do not start with every destructive feature at once.

Recommended progression:

### v0.1
- connect/disconnect
- list folders/files
- upload file
- download file
- refresh
- navigate up
- settings load/save
- visible logs

### v0.2
- delete
- move
- rename
- mkdir
- overwrite confirmation
- improved path handling

### v0.3
- dual-pane polish
- progress bar
- better dialogs
- read-only mode option
- nicer connection handling

### v1.0
- stable EXE packaging
- practical enough for normal non-technical use
- localization support
- refined settings
- generally less ugly, but still intentionally simple

## Roadmap

### Stage 0 - bootstrap
- create repo skeleton
- add README
- define module structure
- define constants and shared strings
- decide initial port and settings file location

### Stage 1 - core protocol skeleton
- implement protocol constants
- implement packet framing
- implement JSON command exchange
- add AUTH and PING
- add basic error reporting

### Stage 2 - server foundation
- choose shared root folder
- start/stop listening server
- path safety checks
- handle LIST requests
- basic logging

### Stage 3 - client foundation
- connect/disconnect UI
- send AUTH and LIST
- show remote folder contents
- basic navigation
- local file list

### Stage 4 - transfer foundation
- upload file
- download file
- chunked transfer
- progress reporting
- overwrite policy handling

### Stage 5 - file operations
- delete
- move
- rename
- mkdir
- confirmation dialogs

### Stage 6 - settings and polish
- remember last settings
- improve logs
- improve error dialogs
- lock down path validation
- test ugly corner cases

### Stage 7 - packaging
- PyInstaller build
- test on Win11
- test on older Windows if still targeted
- prepare release notes

## Naming

Project name chosen in chat:
- Jacammander

The name intentionally hints at a small commander-style file utility while keeping the Jacana flavor.

## Non-goals for early versions

To avoid bloat, early versions should not chase:
- modern flashy UI frameworks
- thumbnails/previews
- drag and drop
- search indexing
- fancy themes
- internet exposure
- enterprise security cosplay

The project should earn complexity, not start with it.

## Summary

Jacammander is intended as a small modular Python LAN file manager/transfer tool designed for simple home-network file exchange between Windows machines, including awkward old/new combinations.

The current direction is:
- English-first
- modular
- Tkinter GUI
- Python sockets
- JSON control protocol plus chunked file transfer
- settings separated from GUI and core logic
- shared logger/debug layer
- easy path toward EXE packaging

In short: a practical little LAN goblin built to avoid SMB misery without dragging in unnecessary infrastructure.
