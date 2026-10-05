# Folder Preview

**Folder Preview** is a lightweight Windows utility that turns ordinary desktop folders into interactive widget-windows. Hovering the cursor over a folder automatically displays a pop-up "pocket" with its contents, eliminating unnecessary clicks, opening File Explorer, and cluttering your screen with windows.

## Current Functionality (Version 3.0😁)

- **Intelligent Recognition:** The script detects when the cursor is hovering over desktop folders, correctly handling localized system folders and OneDrive paths via the Windows Shell API.
- **Interactive & Polished UI:** The pop-up features smooth fade-in/out animations, a clickable file list for quick launching, and custom scrollbar styling. The window automatically adjusts its height based on the file count.
- **Extensive Customization:** Includes a GUI Settings window to toggle Dark/Light themes, display human-readable file sizes, and adjust hover delays or maximum file limits.
- **System Integration:** Features a single-instance lock to prevent duplicate processes, an optional Windows Startup autorun toggle, and DPI independence for screens with 125%+ scaling.
- **Tray Management:** The program runs silently in the background. The system tray icon allows you to access settings, view execution logs, pause the widgets temporarily, or exit safely.

## Tech Stack

- **Python 3.10+**
- **PyQt6**
- **uiautomation** & **comtypes**
- **ctypes**
- **Pillow**

## Project Structure

Based on the current modular architecture:

```text
windows_reincarnation/
│
├── main.py                # Entry point, single-instance lock, and thread orchestrator
├── icon.ico               # Custom icon for the tray and compiled.exe
├── .gitignore             # Git ignore rules
├── README.md              # Documentation
├── LICENSE                # MIT License
│
├── backend/               # System logic ("backend")
│   ├── __init__.py
│   ├── autorun.py         # Windows Registry integration for startup execution
│   ├── config_manager.py  # Saving and loading settings (settings.json in LOCALAPPDATA)
│   ├── file_reader.py     # Parsing folder contents on the disk
│   ├── icon_extractor.py  # Extracting and caching system icons
│   ├── mouse_tracker.py   # Cursor tracking and physical DPI calculation
│   └── win_api.py         # Interaction with Windows UI and Shell API
│
└── ui/                    # User Interface ("frontend")
    ├── __init__.py
    ├── pocket_window.py   # Dynamic widget window, animations, and delegates
    ├── settings_window.py # GUI window for program settings management
    ├── styles.py          # Dynamic UI styling (Dark/Light QSS themes)
    └── tray_icon.py       # Windows system tray integration and log access
```

## Installation and Usage

### Option 1: Standalone Build (Recommended for standard users)

You don't need Python installed to use the app.

1.  Download the compiled `ProjectReincarnation.zip` release.
2.  Extract the folder to a permanent location on your PC.
3.  Run `ProjectReincarnation.exe` from inside the folder.  
    _Note: Windows SmartScreen might flag the app as from an "Unknown Publisher". This is normal for unsigned indie software. Click **More info** -> **Run anyway**._

### Option 2: Running from Source

1.  Ensure Python 3.10+ is installed and added to your system `PATH`.
2.  Install the required dependencies via the command line:
    ```Bash
    pip install PyQt6 uiautomation comtypes Pillow
    ```
3.  Run the main application file:
    ```Bash
    py main.py
    ```

## Building the Executable

To package the app into a standalone directory using PyInstaller (bypassing strict antivirus false-positives):

```Bash
py -m PyInstaller --noconfirm --windowed --icon="icon.ico" --add-data="icon.ico;." --name="ProjectReincarnation" main.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
