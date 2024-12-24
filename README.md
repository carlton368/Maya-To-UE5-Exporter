# Maya to UE5 Exporter

A Python-based Maya tool that simplifies the process of exporting selected 3D meshes from Autodesk Maya to Unreal Engine 5. This tool provides a custom UI allowing you to configure FBX export settings, transform values, texture export options, and metadata before exporting. 

## Features

1. **Maya Export Settings**  
   - Enable or disable smoothing groups, tangents, and instance preservation.  
   - Adjust transform settings (rotation, scale, translation) to suit Unreal Engine's coordinate system.

2. **Texture Export**  
   - Optionally export and/or copy all relevant textures to a specified folder.
   - Each export groups textures under a folder named after the asset.

3. **Metadata & JSON Preview**  
   - Store additional metadata (author, project, version, custom properties) in a JSON file alongside the exported FBX.
   - Live preview of the JSON settings within the UI.
   - Copy the JSON directly to your clipboard if needed.

4. **Unreal Import Settings**  
   - Provide hints for collision generation, lightmap UVs, and uniform scaling to guide the Unreal import process.

5. **Simple UI**  
   - Built with PySide2/Qt for an intuitive, Maya-native interface.
   - Real-time selection updates and status feedback.

## Installation

1. **Requirements**  
   - Maya 2017+  
   - Maya's `fbxmaya` plugin (comes standard with Maya, must be loaded).  
   - [PySide2](https://pypi.org/project/PySide2/) for UI.  
   - [shiboken2](https://pypi.org/project/PySide2/) for QWidget wrapping.  

2. **Script Setup**  
   - Place the `MayaUE5Exporter.py` script in a location accessible to Maya (e.g., in your Maya scripts folder).
   - (Optional) Add that folder to your Maya `PYTHONPATH` or your userSetup file so it can be easily imported.

3. **Load Plugin**  
   - In Maya, ensure the **fbxmaya** plugin is enabled:
     ```python
     cmds.loadPlugin('fbxmaya')
     ```

## Usage

### Opening the UI

In a Python tab within Maya's **Script Editor** or a shelf button, run:

```python
import MayaUE5Exporter
MayaUE5Exporter.show_exporter()
```

> **Note:** If you placed the file under a different name/path, adjust the import statement accordingly.

### UI Overview

1. **Export Path**  
   - Choose or type the destination FBX file path.

2. **Asset Naming**  
   - Optionally specify a custom asset name. If left blank, the exporter will use the base name of your chosen file path.

3. **Maya Export Settings**  
   - **Smoothing Groups**: Preserves smoothing group data.  
   - **Export Tangents**: Exports tangents and binormals.  
   - **Preserve Instances**: Maintains instances within the exported FBX.

4. **Transform Settings**  
   - **Rotation (X/Y/Z)**: Adjust the exported mesh's rotation.  
   - **(Future) Scale / Translation**: Currently locked to default in the sample, but you can extend if needed.

5. **Additional Metadata**  
   - **Author, Project, Version, Description**: Enter freeform text for metadata.  
   - **Tags**: Add comma-separated tags.  
   - **Custom Properties**: Add key-value pairs that will be stored in the JSON.

6. **Texture Settings**  
   - **Export Textures**: Toggle texture exporting.  
   - **Texture Folder**: Choose a directory where textures should be saved.  
   - **Copy Textures to Export Path**: Copy the used textures to the designated folder.

7. **Unreal Import Settings**  
   - **Auto Generate Collision**: Suggest collision generation in Unreal.  
   - **Generate Lightmap UVs**: Suggest automatic lightmap UV creation.  
   - **Scale Factor**: Suggest a uniform scale in Unreal (multiplies the imported mesh size).

8. **JSON Preview**  
   - Shows the combined configuration in real-time.  
   - Use **Copy JSON** to copy to your clipboard.

9. **Buttons**  
   - **Reset to Defaults**: Restores the default settings.  
   - **Export**: Exports selected objects to an FBX and writes a JSON alongside the exported file.

### Exporting

1. **Select Objects**: In Maya's viewport or Outliner, select the objects you want to export.  
2. **Configure Settings**: Adjust any relevant export, texture, or metadata settings in the UI.  
3. **Set Export Path**: Click **Browse** next to *Export Path*, then pick/enter an `.fbx` filename.  
4. **(Optional) Set Texture Path**: If exporting textures, define the folder or check *Copy Textures*.  
5. **Export**: Press **Export**.  
   - The FBX and a `.json` file (e.g., `SM_MyAsset.fbx` and `SM_MyAsset_metadata_fbx.json`) will be generated in the chosen directory.  
6. **Check Status**: The status bar at the bottom indicates success or failure.

## Default Settings

By default, the `MayaUE5ExportSettings` class initializes with:

```json
{
    "geometry": {
        "smoothing_groups": true,
        "tangents_and_binormals": true,
        "preserve_instances": true,
        "preserve_edge_orientation": true,
        "turbosmooth": true
    },
    "coordinate_system": {
        "up_axis": "z",
        "unit_system": "cm"
    },
    "transform": {
        "rotation": [0, 90, 0],
        "scale": [1, 1, 1],
        "translation": [0, 0, 0]
    },
    "textures": {
        "export_textures": false,
        "texture_folder": "",
        "copy_textures": false
    },
    "unreal_import_settings": {
        "auto_generate_collision": true,
        "generate_lightmap_uvs": true,
        "import_materials": true,
        "import_textures": false,
        "combine_meshes": false,
        "normal_import_method": "ComputeNormals",
        "normal_generation_method": "MikkTSpace"
    },
    "metadata": {
        "author": "",
        "date_created": "",
        "project": "",
        "version": "",
        "description": "",
        "tags": [],
        "custom_properties": {}
    }
}
```

> Some fields (e.g., `preserve_edge_orientation`, `turbosmooth`, etc.) are placeholders for potential future usage. Not all are exposed directly in the UI but can be controlled programmatically.

## Customization

The exporter can be extended by editing `MayaUE5ExportSettings`:

- **Adding Additional Settings**  
  Define new keys under `default_settings` and modify the `get_maya_export_options()` method or the UI to reflect those changes.

- **Modifying the UI**  
  You can add more UI widgets to the `UE5ExporterUI` class to control new or existing settings. Be sure to hook them into `update_json_preview()` so changes appear in real time.

- **Automation / Batch Export**  
  For batch operations, you can directly call `MayaUE5ExportSettings.export_fbx(...)` multiple times without opening the UI.

## Troubleshooting

1. **FBX Plugin Not Found**  
   - Ensure `fbxmaya` is loaded via Maya Plugin Manager or `cmds.loadPlugin('fbxmaya')`.

2. **No Objects Selected**  
   - The tool requires at least one object selected in Maya to export. Confirm your selection in the Outliner.

3. **Texture Files Not Copied**  
   - Ensure the file nodes are properly connected and the file paths exist.  
   - Confirm your destination folder is writable.

4. **JSON Not Generated**  
   - Check for permission issues in the export directory.  
   - The script creates a JSON next to the `.fbx`—verify you have write permissions.

## License

This script is provided as-is under the [MIT License](https://opensource.org/licenses/MIT). You are free to modify and distribute it. Attribution is appreciated but not required.

Happy exporting!