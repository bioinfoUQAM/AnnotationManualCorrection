

# Annotation Correction Tool

**A Tkinter GUI for fast, visual correction of frame-level behavior annotations in videos.**

## Features

- Load a video (`mp4`, `avi`, `mov`, `mkv`) and a CSV annotation file
- Visualize the video frame-by-frame with behavior annotations
- Check/uncheck behaviors using checkboxes or keyboard shortcuts
- Navigate using "Previous", "Next", or jump directly to a frame
- Apply selected behaviors to a range of frames
- Save corrected annotations to CSV

## Prerequisites

- Python 3.7+
- Required packages:
  - `opencv-python`
  - `pandas`
  - `numpy`
  - `Pillow`
- Tkinter comes with standard Python installations

**Install dependencies:**
```bash
pip install opencv-python pandas numpy pillow
```

## Usage

1. **Save the script** (e.g., `annotation_correction_tool.py`) in your project folder.
2. **Run the tool:**
   ```bash
   python annotation_correction_tool.py
   ```

3. In the GUI:
   - **Fichier → Charger Vidéo**: Select a video file.
   - **Fichier → Charger Annotations CSV**: Select your CSV (format described below).
   - Use navigation controls to browse frames.
   - Edit behaviors via checkboxes or shortcut keys.
   - Use "Appliquer aux frames sélectionnées" to apply changes to a range.
   - **Fichier → Sauvegarder** or **Sauvegarder sous...** to save your work.

## Input CSV Format

The annotations CSV must have:
- `Frame` column (with frame numbers, usually starting from 1)
- One column per behavior; each cell is 0 (absent) or 1 (present)

Example:
```csv
Frame,Grooming,Feeding,Resting
1,0,1,0
2,1,0,1
3,0,1,0
```

## Keyboard Shortcuts

- Each behavior is auto-assigned a shortcut (first available letter)
- Checkbox label shows the shortcut, e.g. `Grooming [G]`
- Press the shortcut key to quickly toggle that behavior

## Screenshots

*coming soon*

## License

*Add your license here (MIT, GPL, etc).*

## Credits

Developed by Lina AGGOUNE.