import bpy
import os
import subprocess
import shlex
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

def get_backend_script_path():
    return os.path.join(os.path.dirname(__file__), "backend.py")

class NODE_OT_send_to_library(bpy.types.Operator, ExportHelper):
    """Save the selected datablock to an external library file"""
    bl_idname = "node.send_to_library"
    bl_label = "Save Application"
    bl_options = {'REGISTER'}

    # ExportHelper mixin handles the "filepath" property and file selection UI
    filename_ext = ".blend"
    
    filter_glob: StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,
    )

    datablock_name: StringProperty(name="Datablock Name", options={'HIDDEN'})
    datablock_type: StringProperty(name="Datablock Type", options={'HIDDEN'})
    
    # Asset metadata fields
    new_name: StringProperty(
        name="New Name",
        description="Name for the asset in the library",
        default=""
    )
    description: StringProperty(
        name="Description",
        description="Asset description",
        default=""
    )
    author: StringProperty(
        name="Author",
        description="Asset author",
        default=""
    )
    copyright: StringProperty(
        name="Copyright",
        description="Asset copyright information",
        default=""
    )
    license: StringProperty(
        name="License",
        description="Asset license",
        default=""
    )

    append_only: BoolProperty(
        name="Append Only (No Asset)",
        description="Just append the object/node without marking it as an asset. Also ensures it's a single user.",
        default=False
    )

    save_current: BoolProperty(
        name="Save Current File",
        description="Save the current file before trying to send",
        default=False
    )

    def invoke(self, context, event):
        # Pre-fill new_name with the original datablock name
        if not self.new_name:
            self.new_name = self.datablock_name
        
        # We override invoke to ensure the file selector opens
        # The 'filepath' should have been pre-set by the caller (select_library)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        """Draw the file dialog UI with metadata fields"""
        layout = self.layout
        
        layout.prop(self, "new_name")
        layout.separator()
        layout.prop(self, "description")
        layout.prop(self, "author")
        layout.prop(self, "copyright")
        layout.prop(self, "license")
        
        layout.separator()
        layout.prop(self, "append_only")
        layout.prop(self, "save_current")

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}

        # 1. Validation
        source_file = bpy.data.filepath
        if not source_file:
            self.report({'ERROR'}, "Current file must be saved before sending assets.")
            return {'CANCELLED'}
        
        if bpy.data.is_dirty:
            if self.save_current:
                #save the file
                bpy.ops.wm.save_mainfile()
            else:
                self.report({'ERROR'}, "Please save your current file first. The background process needs the latest changes on disk.")
                return {'CANCELLED'}

        # 2. Prepare Command
        blender_bin = bpy.app.binary_path
        backend_script = get_backend_script_path()
        
        # Construct arguments
        # Using list format for subprocess avoids shell injection issues
        cmd = [
            blender_bin,
            "--background",
            "-noaudio", # Optimize startup
            "--python", backend_script,
            "--",
            "--source_file", source_file,
            "--target_file", self.filepath,
            "--datablock_type", self.datablock_type,
            "--datablock_name", self.datablock_name,
            "--new_name", self.new_name,
            "--description", self.description,
            "--author", self.author,
            "--copyright", self.copyright,
            "--license", self.license
        ]

        if self.append_only:
             cmd.append("--append_only")
        
        print(f"Executing: {' '.join(cmd)}")
        self.report({'INFO'}, f"Sending {self.datablock_name} to library...")
        
        # 3. Execution
        context.window.cursor_set("WAIT")
        try:
            # Check for Windows specifically if we want to hide the console window?
            # Usually not needed if we want to capture output, but for user experience:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Blocking call - waits for blender to finish
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo
            )
            
            # 4. Result Handling
            if result.returncode == 0:
                self.report({'INFO'}, f"Success! Asset saved to {os.path.basename(self.filepath)}")
                # We could log result.stdout to console if needed
                print(result.stdout)
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to send asset. Check system console for details.")
                print("--- Backend STDOUT ---")
                print(result.stdout)
                print("--- Backend STDERR ---")
                print(result.stderr)
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"System error: {str(e)}")
            return {'CANCELLED'}
        finally:
            context.window.cursor_set("DEFAULT")

class NODE_OT_select_library_item(bpy.types.Operator):
    """Internal operator to select a specific library from the menu"""
    bl_idname = "node.select_library_item"
    bl_label = "Select specific library"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    library_path: StringProperty()
    datablock_name: StringProperty()
    datablock_type: StringProperty()
    
    def execute(self, context):
        if not self.library_path:
            return {'CANCELLED'}
            
        # Prepare path for next step
        # Default filename = datablock name
        safe_name = bpy.path.clean_name(self.datablock_name)
        file_path = os.path.join(self.library_path, safe_name + ".blend")

        # Invoke the file save operator
        bpy.ops.node.send_to_library(
            'INVOKE_DEFAULT', 
            filepath=file_path,
            datablock_name=self.datablock_name,
            datablock_type=self.datablock_type
        )
        return {'FINISHED'}

def draw_library_items(layout, context, datablock_name, datablock_type):
    libs = context.preferences.filepaths.asset_libraries
    if not libs:
        layout.label(text="No Asset Libraries Found")
        return
        
    for lib in libs:
        op = layout.operator("node.select_library_item", text=lib.name, icon='ASSET_MANAGER')
        op.library_path = lib.path
        op.datablock_name = datablock_name
        op.datablock_type = datablock_type

class NODE_MT_send_node_to_library(bpy.types.Menu):
    bl_label = "Node => Asset Library"
    bl_idname = "NODE_MT_send_node_to_library"
    
    def draw(self, context):
        if hasattr(context, 'active_node') and context.active_node and context.active_node.type == 'GROUP' and context.active_node.node_tree:
             draw_library_items(self.layout, context, context.active_node.node_tree.name, "NodeTree")
        else:
             self.layout.label(text="No Node Group Active")

class NODE_MT_send_material_to_library(bpy.types.Menu):
    bl_label = "Material => Asset Library"
    bl_idname = "NODE_MT_send_material_to_library"

    def draw(self, context):
        mat = getattr(context, 'material', None)
        if mat:
            draw_library_items(self.layout, context, mat.name, "Material")
        else:
            self.layout.label(text="No Material Active")

def draw_node_context_menu(self, context):
    layout = self.layout
    
    # 1. Node Group
    node = getattr(context, 'active_node', None)
    if node:
        # Check if node is selected AND is a group
        # active_node can be set even if unselected, so we must check node.select
        is_selected_group = bool(node.select and node.type == 'GROUP' and node.node_tree)
        layout.separator()
        col = layout.column()
        col.enabled = is_selected_group
        col.menu("NODE_MT_send_node_to_library", text="Group Node => Asset Library", icon='ASSET_MANAGER')
    
    # 2. Material (only if in Shader Editor)
    if hasattr(context, 'space_data') and context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'ShaderNodeTree':
        if getattr(context, 'material', None):
             layout.separator()
             layout.menu("NODE_MT_send_material_to_library", text="Current Material => Asset Library", icon='ASSET_MANAGER')

def draw_material_context_menu(self, context):
    material = context.material
    if material:
        layout = self.layout
        layout.separator()
        layout.menu("NODE_MT_send_material_to_library", text="CurrentMaterial => Asset Library", icon='ASSET_MANAGER')

class OBJECT_MT_send_to_library(bpy.types.Menu):
    bl_label = "Object => Asset Library"
    bl_idname = "OBJECT_MT_send_to_library"

    def draw(self, context):
        obj = context.active_object
        if obj:
            draw_library_items(self.layout, context, obj.name, "Object")
        else:
            self.layout.label(text="No Object Active")

def draw_object_context_menu(self, context):
    layout = self.layout
    obj = context.active_object
    if obj:
        layout.separator()
        layout.menu("OBJECT_MT_send_to_library", text="Current Object => Asset Library", icon='ASSET_MANAGER')
