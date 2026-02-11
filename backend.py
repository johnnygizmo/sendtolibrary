import bpy
import sys
import argparse
import os

def get_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--source_file", required=True, help="Path to the source .blend file")
    parser.add_argument("--target_file", required=True, help="Path to the target library .blend file")
    parser.add_argument("--datablock_type", required=True, help="Type of datablock (e.g., NodeTree, Material)")
    parser.add_argument("--datablock_name", required=True, help="Name of the datablock")
    
    return parser.parse_args(argv)

def main():
    args = get_args()

    print(f"Starting Send-To-Library Operation")
    print(f"Source: {args.source_file}")
    print(f"Target: {args.target_file}")
    print(f"Asset: {args.datablock_name} ({args.datablock_type})")

    # 1. Setup Target File
    # If target exists, open it. If not, start clean.
    if os.path.exists(args.target_file):
        try:
            bpy.ops.wm.open_mainfile(filepath=args.target_file)
        except Exception as e:
            print(f"Error opening file: {e}")
            sys.exit(1)
    else:
        # Create a new file (remove default cube, etc)
        bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Append Data
    # The 'directory' parameter in append expects: /path/to/file.blend/NodeTree/
    # We construct the full path to the internal collection
    
    # Ensure source file path is absolute
    source_file = os.path.abspath(args.source_file)
    
    # Construct directory path inside the blend file
    # Note: Append works by specifying 'filepath' (full path to ID) and 'directory' (path to ID's container)
    # directory format: c:\path\source.blend\NodeTree\
    
    # Windows path safety
    source_dir = os.path.join(source_file, args.datablock_type)
    
    try:
        bpy.ops.wm.append(
            filepath=os.path.join(source_dir, args.datablock_name),
            directory=source_dir,
            filename=args.datablock_name
        )
    except Exception as e:
        print(f"Failed to append: {e}")
        sys.exit(1)

    # 3. Mark as Asset
    # Find the object we just appended
    asset = None
    
    # Resolving the datablock collection based on type
    # This mapping might need expansion for other types
    if args.datablock_type == "NodeTree":
        asset = bpy.data.node_groups.get(args.datablock_name)
    elif args.datablock_type == "Material":
        asset = bpy.data.materials.get(args.datablock_name)
    elif args.datablock_type == "Object":
        asset = bpy.data.objects.get(args.datablock_name)
    # Add other types here as needed
        
    if asset:
        print(f"Marking '{asset.name}' as asset...")
        asset.asset_mark()
        # asset.asset_generate_preview()
        try:
            with bpy.context.temp_override(id=asset, selected_ids=[asset]):
                 bpy.ops.ed.lib_id_generate_preview()
        except Exception as e:
            print(f"Preview generation warning: {e}")
    else:
        print(f"Error: Could not find appended asset '{args.datablock_name}' in target file.")
        sys.exit(1)

    # 4. Save Target
    try:
        bpy.ops.wm.save_as_mainfile(filepath=args.target_file)
        print(f"Successfully saved to {args.target_file}")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
