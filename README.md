# Project Reincarnation (Folder Pockets)

**Folder Pockets** is a lightweight Windows utility that turns ordinary desktop folders into interactive widget-windows. Hovering the cursor over a folder automatically displays a pop-up "pocket" with its contents, eliminating unnecessary clicks and screen clutter from open File Explorer windows.

## Current Functionality Patch 0.8a

- **Intelligent Recognition:** The script detects when the cursor is specifically hovering over a desktop folder icon (ignoring shortcuts, files, and other windows).
- **Invisible Integration:** The window operates in `Tool` mode - it does not appear on the taskbar and does not steal input focus when opened.
- **DPI Independence:** Automatic correction of mouse coordinates during Windows screen scaling (DPI Scaling) via `ctypes`.
- **Smooth UI:** Shows the place of window in feature.

## Tech Stack

- **Python 3.10+**
- **PyQt6** — UI engine, hover delay timers, and the signals/slots system.
- **uiautomation** — reading the `explorer.exe` element tree (interacting with the `SysListView32` class).
- **ctypes & winreg** — low-level Windows API calls for DPI fixing and registry path resolution.

## Project Structure

```text
Project_reincarnation/
│
├── main.py                # Entry point, application orchestrator
├── config.py              # Global settings (timings, UI dimensions)
├── .gitignore             # Git ignore rules
├── README.md              # Documentation
│
├── backend/               # System logic ("brain")
│   ├── __init__.py        # Package initializer
│   ├── file_reader.py     # Parsing folder contents (upcoming)
│   ├── mouse_tracker.py   # Cursor tracking and timers via QTimer
│   └── win_api.py         # Parsing Windows UI elements and path validation
│
└── ui/                    # User Interface ("face")
    ├── __init__.py        # Package initializer
    ├── pocket_window.py   # Widget window configuration (FramelessWindowHint)
    └── styles.py          # UI styling (QSS/CSS, colors, paddings)
```

## Installation and Usage

1.  Ensure Python is installed and added to your `PATH`.
2.  Install the required dependencies:

    ```
    pip install PyQt6 uiautomation

    ```

3.  Run the main application file:

    ```
    python main.py
    or py main.py

    ```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/krinzhanovskyi/Project_reincarnation_28082026/blob/main/LICENSE) file for details.
