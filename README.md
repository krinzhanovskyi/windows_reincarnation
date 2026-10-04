# Project windows_file_preview

**Folder preview** is a lightweight Windows utility that turns ordinary desktop folders into interactive widget-windows. Hovering the cursor over a folder automatically displays a pop-up "pocket" with its contents, eliminating unnecessary clicks, opening File Explorer, and cluttering your screen with windows.

## Current Functionality (Version 2.0)

- **Intelligent Recognition:** The script detects when the cursor is specifically hovering over a **desktop folders** icon, correctly handling even localized system folders via the Windows Shell API.
- **Interactive Interface:** The pop-up window operates in the background. It features a clickable file list for quick launching. The window automatically adjusts its height based on the file count and includes a styled scrollbar.
- **Tray Management:** The program runs in the background and is controlled via the system tray. Features include temporarily pausing the widgets and safely exiting the application.
- **DPI Independence:** Automatic correction of mouse coordinates regardless of Windows screen scaling.

## Tech Stack

- **Python 3.10+**
- **PyQt6**
- **uiautomation**
- **ctypes** `SHGetFileInfoW`.

## Project Structure

Based on the current modular architecture:

```text
windows_reincarnation/
│
├── main.py                # Entry point, application thread orchestrator
├── icon.ico               # Custom icon for the tray and future .exe build
├── .gitignore             # Git ignore rules
├── README.md              # Documentation
├── LICENSE                # MIT License
│
├── backend/               # System logic ("backend")
│   ├── __init__.py
│   ├── config_manager.py  # Saving and loading settings (settings.json)
│   ├── file_reader.py     # Parsing folder contents on the disk
│   ├── icon_extractor.py  # Extracting and caching system/Steam icons
│   ├── mouse_tracker.py   # Cursor tracking and worker thread management
│   └── win_api.py         # Interaction with Windows UI and Shell API
│
└── ui/                    # User Interface ("frontend")
    ├── __init__.py
    ├── pocket_window.py   # Dynamic widget window and scrollbar configuration
    ├── settings_window.py # GUI window for program settings management
    ├── styles.py          # UI styling (if used externally)
    └── tray_icon.py       # Windows system tray integration

```

## Installation and Usage

1.  Ensure Python is installed and added to your system `PATH`.
2.  Install the required dependencies via the command line:

    Bash

    ```
    pip install PyQt6 uiautomation

    ```

3.  Run the main application file:

    Bash

    ```
    py main.py

    ```

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
