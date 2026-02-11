# Send to Library Extension for Blender

This extension allows you to easily "send" a datablock (currently Node Groups) from your current file to an external Asset Library file. It handles creating the target file or opening an existing one, appending the data, marking it as an asset, and saving.

## Installation

1. Open Blender 4.2+.
2. Go to `Edit > Preferences > Get Extensions`.
3. Install from Disk... and select the `send_to_library` folder or zip.

## Setup

Before using, ensure you have configured your Asset Libraries:
1. Go to `Edit > Preferences > File Paths`.
2. Under **Asset Libraries**, add a new library location (a folder on your drive).

## Usage

1. **Save your current work.** The file must be saved to disk for the background process to read the data.
2. Open the Shader or Geometry Node Editor, or the Material Properties panel.
3. Node Context: Right-click a **Group Node**.
4. Material Context: Right-click in the Material list context menu.
5. Hover over **Send to Asset Library**.
6. Select the target **Asset Library** from the submenu.
7. A file save dialog will open in that library folder with a default filename.
   - Select an existing `.blend` file to append to.
   - OR type a new filename to create a new library file.
8. Click **Save Application**.
9. Blender will briefly pause while a background process handles the transfer.
10. A confirmation message "Success! Asset saved..." will appear in the status bar/info area.

## Technical Details

- The extension spawns a background Blender process (`blender --background`).
- It executes a Python script (`backend.py`) that handles the file I/O safely.
- **NodeTree** types are currently supported.

## Troubleshooting

- **"Current file must be saved contents..."**: You must save your .blend file (Ctrl+S) before sending, as the background process reads from the file on disk.
- **"Failed to send asset"**: Check the System Console (`Window > Toggle System Console` on Windows) for detailed error messages from the background process.
