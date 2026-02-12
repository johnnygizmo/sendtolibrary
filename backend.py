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
    parser.add_argument("--new_name", required=True, help="New name for the asset")
    parser.add_argument("--description", default="", help="Asset description")
    parser.add_argument("--author", default="", help="Asset author")
    parser.add_argument("--copyright", default="", help="Asset copyright")
    parser.add_argument("--license", default="", help="Asset license")
    parser.add_argument("--append_only", action="store_true", help="If true, append only and do not mark as asset")
    
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
        if args.append_only:
             print(f"Appended '{asset.name}'. Skipping asset marking (Append Only mode).")
             
             # Make Single User (specifically for Objects)
             if args.datablock_type == "Object":
                 # Ensure the object and its data are single user
                 # This mimics the "Make Single User" -> "Object & Data" checks
                 try:
                    # We can use the make_single_user operator or do it manually via ID user count
                    # But since we are backend, we might not have context.
                    # Manual approach is safer for background.
                    
                    # 1. Make the object itself single user (it technically is, since we just appended it, 
                    # unless it was already there and we re-used it? Append usually makes a new copy if not linked)
                    
                    # However, "Make Single User" primarily affects shared data blocks (Mesh, Material, etc)
                    # For a newly appended object, it might share mesh data if that mesh was already in the file.
                    
                    # Let's use the low-level function provided by the ID
                    # make_local() is about library linking. 
                    # user_clear() removes users.
                    
                    # The user likely wants existing data to be unique to this object.
                    # Equivalent to: Object > Relations > Make Single User > Object & Data
                    
                    if asset.data and asset.data.users > 1:
                        print(f"Making data '{asset.data.name}' single user...")
                        asset.data = asset.data.copy()
                        
                 except Exception as e:
                     print(f"Error making single user: {e}")

        else:
            print(f"Marking '{asset.name}' as asset...")
            
            # Rename the asset if new_name is different
            if args.new_name and args.new_name != asset.name:
                print(f"Renaming asset from '{asset.name}' to '{args.new_name}'")
                asset.name = args.new_name
            
            # Mark as asset
            asset.asset_mark()
            
            # Set metadata fields
            if args.description:
                asset.asset_data.description = args.description
                print(f"Set description: {args.description}")
            if args.author:
                asset.asset_data.author = args.author
                print(f"Set author: {args.author}")
            if args.copyright:
                asset.asset_data.copyright = args.copyright
                print(f"Set copyright: {args.copyright}")
            if args.license:
                asset.asset_data.license = args.license
                print(f"Set license: {args.license}")
            
            # Generate preview
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
