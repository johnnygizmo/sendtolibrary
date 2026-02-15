import bpy
import importlib

import sys
import os

# Support running as a script (e.g. from VS Code)
if __name__ == "__main__":
    if "operators" not in locals():
       # Ensure current directory is in path so we can import 'operators'
       sys.path.append(os.path.dirname(__file__))

if "operators" in locals():
    importlib.reload(operators)
else:
    try:
        from . import operators
    except ImportError:
         # Fallback when running as main script
        import operators

def node_menu_func(self, context):
    operators.draw_node_context_menu(self, context)

def material_menu_func(self, context):
    operators.draw_material_context_menu(self, context)

def object_menu_func(self, context):
    operators.draw_object_context_menu(self, context)

def outliner_menu_func(self, context):
    operators.draw_outliner_context_menu(self, context)

classes = (
    operators.NODE_OT_send_to_library,
    operators.NODE_OT_select_library_item,
    operators.NODE_MT_send_node_to_library,
    operators.NODE_MT_send_material_to_library,
    operators.OBJECT_MT_send_to_library,
    operators.OUTLINER_MT_send_nodetree_to_library,
    operators.OUTLINER_MT_send_material_to_library,
    operators.OUTLINER_MT_send_object_to_library,
    operators.OUTLINER_MT_send_collection_to_library,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Add to Node Editor context menu
    bpy.types.NODE_MT_context_menu.append(node_menu_func)
    # Add to Material context menu
    bpy.types.MATERIAL_MT_context_menu.append(material_menu_func)
    # Add to Object context menu
    bpy.types.VIEW3D_MT_object_context_menu.append(object_menu_func)
    
    # Find and register outliner context menu
    outliner_menus = [name for name in dir(bpy.types) if 'OUTLINER' in name and 'MT' in name]
    registered_outliner = False
    for menu_name in outliner_menus:
        try:
            menu_type = getattr(bpy.types, menu_name)
            if hasattr(menu_type, 'append'):
                menu_type.append(outliner_menu_func)
                registered_outliner = True
                break
        except Exception:
            pass

def unregister():
    bpy.types.NODE_MT_context_menu.remove(node_menu_func)
    bpy.types.MATERIAL_MT_context_menu.remove(material_menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.remove(object_menu_func)
    
    # Try to unregister from all OUTLINER menus
    outliner_menus = [name for name in dir(bpy.types) if 'OUTLINER' in name and 'MT' in name]
    for menu_name in outliner_menus:
        try:
            menu_type = getattr(bpy.types, menu_name)
            if hasattr(menu_type, 'remove'):
                menu_type.remove(outliner_menu_func)
        except (AttributeError, ValueError, TypeError):
            pass
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
