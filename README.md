# JohannClicker

A lightweight desktop auto-clicker inspired by Auto-Clicker by Polar 2.0, rebuilt with a modern UI and extra quality-of-life tools. This version adds JSON import/export for reusable click sequences.

## Features

- Coordinate picker with live overlay (Pick -> click anywhere)
- Queue of cursor positions with per-step delay and L/R click
- Drag-and-drop reordering, duplicate, and delete from a context menu
- Double-click a row to edit delay quickly
- Auto-append option (Pick -> Add) in Settings
- Global hotkey: CTRL+F3 to start/stop
- JSON import/export for sharing click sequences

## Tech stack

- Python 3
- Tkinter + customtkinter (UI)
- pynput (global hotkeys and mouse control)
- Pillow (icon/image handling)

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run from source

```bash
python autoclicker.py
```

## Build and run as an EXE (Windows)

1) Install PyInstaller:

```bash
pip install pyinstaller
```

2) Build the executable (includes the app icon if present):

```bash
pyinstaller --onefile --windowed --icon logo.ico --add-data "logo.png;." autoclicker.py
```

3) Run the exe from the output folder:

```bash
.\dist\autoclicker.exe
```

Notes:
- If you do not have logo.ico or logo.png, remove the related flags.
- The first run may trigger Windows Defender SmartScreen for unsigned executables.

## Usage

1) Click Pick, then click anywhere on screen to capture X/Y.
2) Set delay and left/right click, then Add position.
3) Add multiple rows, reorder as needed.
4) Set Number of Repeats, then Start clicking or press CTRL+F3.
5) Press CTRL+F3 again or Stop clicking to halt.

<img width="1030" height="636" alt="image" src="https://github.com/user-attachments/assets/49f628e5-5dcf-4f30-8e08-bde070992002" />


## Inspiration

The layout and workflow are inspired by Auto-Clicker by Polar 2.0, with added sequence management and JSON import/export to save and reuse click scripts.

## Tips

- Use short delays for rapid clicking and longer delays for scripted workflows.
- Right-click a row to move, duplicate, or delete it.
- Double-click a row to edit its delay in place.

## License

MIT License

Copyright (c) 2026 Tarikuzuma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
