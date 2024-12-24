import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import json
from pathlib import Path
import os
import shutil
from typing import Dict, Optional

def get_maya_window():
    maya_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(maya_window_ptr), QtWidgets.QWidget)

class MayaUE5ExportSettings:
    def __init__(self):
        self.default_settings = {
            "geometry": {
                "smoothing_groups": True,
                "tangents_and_binormals": True,
                "preserve_instances": True,
                "preserve_edge_orientation": True,
                "turbosmooth": True
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
                "export_textures": False,
                "texture_folder": "",
                "copy_textures": False
            },
            "unreal_import_settings": {
                "auto_generate_collision": True,
                "generate_lightmap_uvs": True,
                "import_materials": True,
                "import_textures": False,
                "combine_meshes": False,
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
    
    def get_maya_export_options(self) -> str:
        options = [
            "groups=1",
            "ptgroups=1",
            "materials=1",
            "smoothing=1",
            f"smoothingGroups={1 if self.default_settings['geometry']['smoothing_groups'] else 0}",
            "preserveInstances=1",
            f"tangents={1 if self.default_settings['geometry']['tangents_and_binormals'] else 0}",
            "animations=0",
            "skeleton=0",
            f"up={self.default_settings['coordinate_system']['up_axis']}",
            "unitconversion=cm",
            "exportUnrealCompatible=1",
            f"rotateX={self.default_settings['transform']['rotation'][0]}",
            f"rotateY={self.default_settings['transform']['rotation'][1]}",
            f"rotateZ={self.default_settings['transform']['rotation'][2]}"
        ]
        return ";".join(options)
    
    def _copy_textures(self, shader_nodes, texture_dir: Path):
        copied_files = set()
        
        for shader in shader_nodes:
            file_nodes = cmds.listConnections(shader, type="file") or []
            
            for file_node in file_nodes:
                texture_path = cmds.getAttr(f"{file_node}.fileTextureName")
                if texture_path and os.path.exists(texture_path):
                    base_name = os.path.basename(texture_path)
                    target_path = texture_dir / base_name
                    if str(target_path) not in copied_files:
                        shutil.copy2(texture_path, target_path)
                        copied_files.add(str(target_path))
    
    def export_fbx(self, export_path: str, asset_name: str = "", texture_path: str = "") -> bool:
        try:
            if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
                cmds.loadPlugin('fbxmaya')
            
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not asset_name:
                asset_name = export_path.stem
            
            prefix = "SM_" 
            final_name = f"{prefix}{asset_name}"
            fbx_path = export_path.parent / f"{final_name}.fbx"
            
            if self.default_settings["textures"]["export_textures"] and texture_path:
                texture_dir = Path(texture_path) / final_name / "textures"
                texture_dir.mkdir(parents=True, exist_ok=True)
                
                shader_nodes = set()
                for obj in cmds.ls(selection=True):
                    shapes = cmds.listRelatives(obj, shapes=True) or []
                    for shape in shapes:
                        shading_engines = cmds.listConnections(shape, type="shadingEngine") or []
                        for se in shading_engines:
                            materials = cmds.listConnections(f"{se}.surfaceShader") or []
                            shader_nodes.update(materials)
                
                if self.default_settings["textures"]["copy_textures"]:
                    self._copy_textures(shader_nodes, texture_dir)
            
            cmds.file(
                str(fbx_path),
                force=True,
                options=self.get_maya_export_options(),
                typ="FBX export",
                preserveReferences=True,
                exportSelected=True
            )
            
            settings_path = fbx_path.parent / f"{final_name}_metadata_fbx.json"
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.default_settings, f, indent=4)
            
            return True
            
        except Exception as e:
            print(f"Error exporting FBX: {str(e)}")
            return False
    
    def modify_settings(self, settings_dict: Dict) -> None:
        def update_nested_dict(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict:
                    update_nested_dict(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        update_nested_dict(self.default_settings, settings_dict)

class JsonPreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(JsonPreviewWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        
        header_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Export Settings Preview")
        title.setStyleSheet("font-weight: bold;")
        copy_btn = QtWidgets.QPushButton("Copy JSON")
        copy_btn.setMaximumWidth(100)
        copy_btn.clicked.connect(self.copy_json)
        
        header_layout.addWidget(title)
        header_layout.addWidget(copy_btn)
        layout.addLayout(header_layout)
        
        self.json_preview = QtWidgets.QPlainTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.json_preview.setFont(font)
        
        palette = self.json_preview.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#2b2b2b"))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#a9b7c6"))
        self.json_preview.setPalette(palette)
        
        layout.addWidget(self.json_preview)
    
    def update_preview(self, settings: Dict):
        try:
            json_str = json.dumps(settings, indent=4)
            json_str = json_str.replace('":', '":').replace('true', 'true').replace('false', 'false')
            self.json_preview.setPlainText(json_str)
        except Exception as e:
            self.json_preview.setPlainText(f"Error formatting JSON: {str(e)}")
    
    def copy_json(self):
        QtWidgets.QApplication.clipboard().setText(self.json_preview.toPlainText())

class UE5ExporterUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_window()):
        super(UE5ExporterUI, self).__init__(parent)
        
        self.setWindowTitle("Maya to UE5 Exporter")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        self.settings = MayaUE5ExportSettings()
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        path_group = QtWidgets.QGroupBox("Export Path")
        path_layout = QtWidgets.QHBoxLayout()
        self.path_field = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_field)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        left_layout.addWidget(path_group)
        
        naming_group = QtWidgets.QGroupBox("Asset Naming")
        naming_layout = QtWidgets.QVBoxLayout()
        self.asset_name = QtWidgets.QLineEdit()
        self.asset_name.setPlaceholderText("Asset Name (optional)")
        naming_layout.addWidget(QtWidgets.QLabel("Asset Name:"))
        naming_layout.addWidget(self.asset_name)
        naming_group.setLayout(naming_layout)
        left_layout.addWidget(naming_group)
        
        maya_group = QtWidgets.QGroupBox("Maya Export Settings")
        maya_layout = QtWidgets.QVBoxLayout()
        
        self.smoothing_check = QtWidgets.QCheckBox("Smoothing Groups")
        self.smoothing_check.setChecked(True)
        self.smoothing_check.stateChanged.connect(self.update_json_preview)
        
        self.tangents_check = QtWidgets.QCheckBox("Export Tangents")
        self.tangents_check.setChecked(True)
        self.tangents_check.stateChanged.connect(self.update_json_preview)
        
        self.instances_check = QtWidgets.QCheckBox("Preserve Instances")
        self.instances_check.setChecked(True)
        self.instances_check.stateChanged.connect(self.update_json_preview)
        
        maya_layout.addWidget(self.smoothing_check)
        maya_layout.addWidget(self.tangents_check)
        maya_layout.addWidget(self.instances_check)
        maya_group.setLayout(maya_layout)
        left_layout.addWidget(maya_group)

        transform_group = QtWidgets.QGroupBox("Transform Settings")
        transform_layout = QtWidgets.QVBoxLayout()
        
        rotation_layout = QtWidgets.QHBoxLayout()
        rotation_layout.addWidget(QtWidgets.QLabel("Rotation:"))
        
        self.rot_x = QtWidgets.QSpinBox()
        self.rot_y = QtWidgets.QSpinBox()
        self.rot_z = QtWidgets.QSpinBox()
        
        for rot in [self.rot_x, self.rot_y, self.rot_z]:
            rot.setRange(-360, 360)
            rot.setSingleStep(90)
            rot.valueChanged.connect(self.update_json_preview)
        
        self.rot_y.setValue(90)
        
        rotation_layout.addWidget(QtWidgets.QLabel("X:"))
        rotation_layout.addWidget(self.rot_x)
        rotation_layout.addWidget(QtWidgets.QLabel("Y:"))
        rotation_layout.addWidget(self.rot_y)
        rotation_layout.addWidget(QtWidgets.QLabel("Z:"))
        rotation_layout.addWidget(self.rot_z)
        
        transform_layout.addLayout(rotation_layout)
        transform_group.setLayout(transform_layout)
        left_layout.addWidget(transform_group)
        
        metadata_group = QtWidgets.QGroupBox("Additional Metadata")
        metadata_layout = QtWidgets.QVBoxLayout()
        
        self.metadata_fields = {}
        basic_fields = {
            "author": "Author",
            "project": "Project Name",
            "version": "Version",
            "description": "Description"
        }
        
        for key, label in basic_fields.items():
            field_layout = QtWidgets.QHBoxLayout()
            field_layout.addWidget(QtWidgets.QLabel(f"{label}:"))
            self.metadata_fields[key] = QtWidgets.QLineEdit()
            field_layout.addWidget(self.metadata_fields[key])
            metadata_layout.addLayout(field_layout)
        
        tag_layout = QtWidgets.QHBoxLayout()
        tag_layout.addWidget(QtWidgets.QLabel("Tags:"))
        self.tag_input = QtWidgets.QLineEdit()
        self.tag_input.setPlaceholderText("Enter tags separated by commas")
        tag_layout.addWidget(self.tag_input)
        metadata_layout.addLayout(tag_layout)
        
        self.custom_properties = QtWidgets.QTableWidget()
        self.custom_properties.setColumnCount(2)
        self.custom_properties.setHorizontalHeaderLabels(["Key", "Value"])
        self.custom_properties.horizontalHeader().setStretchLastSection(True)
        
        custom_buttons = QtWidgets.QHBoxLayout()
        add_prop_btn = QtWidgets.QPushButton("Add Property")
        remove_prop_btn = QtWidgets.QPushButton("Remove Property")
        
        add_prop_btn.clicked.connect(self.add_custom_property)
        remove_prop_btn.clicked.connect(self.remove_custom_property)
        
        custom_buttons.addWidget(add_prop_btn)
        custom_buttons.addWidget(remove_prop_btn)
        
        metadata_layout.addWidget(self.custom_properties)
        metadata_layout.addLayout(custom_buttons)
        
        metadata_group.setLayout(metadata_layout)
        left_layout.addWidget(metadata_group)
        
        texture_group = QtWidgets.QGroupBox("Texture Settings")
        texture_layout = QtWidgets.QVBoxLayout()
        
        self.export_textures = QtWidgets.QCheckBox("Export Textures")
        self.export_textures.stateChanged.connect(self.update_texture_ui)
        
        texture_path_layout = QtWidgets.QHBoxLayout()
        self.texture_path = QtWidgets.QLineEdit()
        self.texture_path.setEnabled(False)
        texture_browse_btn = QtWidgets.QPushButton("Browse")
        texture_browse_btn.clicked.connect(self.browse_texture_path)
        texture_path_layout.addWidget(self.texture_path)
        texture_path_layout.addWidget(texture_browse_btn)
        
        self.copy_textures = QtWidgets.QCheckBox("Copy Textures to Export Path")
        self.copy_textures.setEnabled(False)
        
        texture_layout.addWidget(self.export_textures)
        texture_layout.addLayout(texture_path_layout)
        texture_layout.addWidget(self.copy_textures)
        texture_group.setLayout(texture_layout)
        left_layout.addWidget(texture_group)
        
        unreal_group = QtWidgets.QGroupBox("Unreal Import Settings")
        unreal_layout = QtWidgets.QVBoxLayout()
        
        self.collision_check = QtWidgets.QCheckBox("Auto Generate Collision")
        self.collision_check.setChecked(True)
        self.collision_check.stateChanged.connect(self.update_json_preview)
        
        self.lightmap_check = QtWidgets.QCheckBox("Generate Lightmap UVs")
        self.lightmap_check.setChecked(True)
        self.lightmap_check.stateChanged.connect(self.update_json_preview)
        
        # Scale Factor
        scale_layout = QtWidgets.QHBoxLayout()
        scale_layout.addWidget(QtWidgets.QLabel("Scale Factor:"))
        self.scale_spin = QtWidgets.QDoubleSpinBox()
        self.scale_spin.setRange(0.01, 100.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.valueChanged.connect(self.update_json_preview)
        scale_layout.addWidget(self.scale_spin)
        
        unreal_layout.addWidget(self.collision_check)
        unreal_layout.addWidget(self.lightmap_check)
        unreal_layout.addLayout(scale_layout)
        unreal_group.setLayout(unreal_layout)
        left_layout.addWidget(unreal_group)
        
        self.selection_label = QtWidgets.QLabel("Selected: No objects selected")
        left_layout.addWidget(self.selection_label)
        
        button_layout = QtWidgets.QHBoxLayout()
        
        reset_btn = QtWidgets.QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_settings)
        
        export_btn = QtWidgets.QPushButton("Export")
        export_btn.setStyleSheet("background-color: #2ecc71; color: white;")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(export_btn)
        left_layout.addLayout(button_layout)
        
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        
        self.json_preview = JsonPreviewWidget()
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.json_preview)
        splitter.setSizes([400, 400])  
        
        main_layout.addWidget(splitter)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_selection_info)
        self.timer.start(500)
        
        self.update_json_preview()
        
    def update_selection_info(self):
        selection = cmds.ls(selection=True)
        if selection:
            self.selection_label.setText(f"Selected: {len(selection)} object(s)")
        else:
            self.selection_label.setText("Selected: No objects selected")
    
    def update_texture_ui(self):
        enabled = self.export_textures.isChecked()
        self.texture_path.setEnabled(enabled)
        self.copy_textures.setEnabled(enabled)
        self.update_json_preview()
    
    def update_json_preview(self):
        current_settings = self.get_current_settings()
        self.settings.modify_settings(current_settings)
        self.json_preview.update_preview(self.settings.default_settings)
            
    def browse_path(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export FBX",
            "",
            "FBX Files (*.fbx)"
        )
        if file_path:
            self.path_field.setText(file_path)
            
    def browse_texture_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Texture Export Directory"
        )
        if path:
            self.texture_path.setText(path)
            self.update_json_preview()
            
    def reset_settings(self):
        self.smoothing_check.setChecked(True)
        self.tangents_check.setChecked(True)
        self.instances_check.setChecked(True)
        self.collision_check.setChecked(True)
        self.lightmap_check.setChecked(True)
        self.scale_spin.setValue(1.0)
        self.export_textures.setChecked(False)
        self.copy_textures.setChecked(False)
        self.texture_path.setText("")
        
        self.rot_x.setValue(0)
        self.rot_y.setValue(90)  
        self.rot_z.setValue(0)
        
        for field in self.metadata_fields.values():
            field.clear()
        self.tag_input.clear()
        self.custom_properties.setRowCount(0)
        
        self.update_json_preview()
        
    def show_status(self, message: str, is_error: bool = False):
        color = "#e74c3c" if is_error else "#2ecc71"
        self.status_label.setStyleSheet(f"color: {color}")
        self.status_label.setText(message)
        
    def get_current_settings(self) -> Dict:
        import datetime
        
        return {
            "geometry": {
                "smoothing_groups": self.smoothing_check.isChecked(),
                "tangents_and_binormals": self.tangents_check.isChecked(),
                "preserve_instances": self.instances_check.isChecked()
            },
            "transform": {
                "rotation": [self.rot_x.value(), self.rot_y.value(), self.rot_z.value()],
                "scale": [1, 1, 1],
                "translation": [0, 0, 0]
            },
            "textures": {
                "export_textures": self.export_textures.isChecked(),
                "texture_folder": self.texture_path.text(),
                "copy_textures": self.copy_textures.isChecked()
            },
            "unreal_import_settings": {
                "auto_generate_collision": self.collision_check.isChecked(),
                "generate_lightmap_uvs": self.lightmap_check.isChecked(),
                "import_uniform_scale": self.scale_spin.value()
            },
            "metadata": {
                "author": self.metadata_fields["author"].text(),
                "project": self.metadata_fields["project"].text(),
                "version": self.metadata_fields["version"].text(),
                "description": self.metadata_fields["description"].text(),
                "date_created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tags": [tag.strip() for tag in self.tag_input.text().split(",") if tag.strip()],
                "custom_properties": self.get_custom_properties()
            }
        }
        
    def export(self):
        export_path = self.path_field.text()
        if not export_path:
            self.show_status("Please select export path", True)
            return
            
        selection = cmds.ls(selection=True)
        if not selection:
            self.show_status("Please select objects to export", True)
            return
            
        try:
            self.settings.modify_settings(self.get_current_settings())
            
            texture_path = self.texture_path.text() if self.export_textures.isChecked() else ""
          
            if self.settings.export_fbx(
                export_path, 
                asset_name=self.asset_name.text(),
                texture_path=texture_path
            ):
                self.show_status("Export completed successfully!")
            else:
                self.show_status("Export failed", True)
                
        except Exception as e:
            self.show_status(f"Error: {str(e)}", True)
    def add_custom_property(self):
        row = self.custom_properties.rowCount()
        self.custom_properties.insertRow(row)
        self.custom_properties.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        self.custom_properties.setItem(row, 1, QtWidgets.QTableWidgetItem(""))

    def remove_custom_property(self):
        current_row = self.custom_properties.currentRow()
        if current_row >= 0:
            self.custom_properties.removeRow(current_row)

    def get_custom_properties(self) -> Dict:
        properties = {}
        for row in range(self.custom_properties.rowCount()):
            key = self.custom_properties.item(row, 0)
            value = self.custom_properties.item(row, 1)
            if key and value and key.text().strip():
                properties[key.text().strip()] = value.text().strip()
        return properties

def show_exporter():
    try:
        global ue5_exporter
        ue5_exporter = UE5ExporterUI()
        ue5_exporter.show()
    except Exception as e:
        print(f"Error showing exporter: {str(e)}")


if __name__ == "__main__":
    show_exporter()