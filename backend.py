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
    # Map datablock types to their collections
    datablock_collections = {
        "NodeTree": bpy.data.node_groups,
        "Material": bpy.data.materials,
        "Object": bpy.data.objects,
    }
    
    collection = datablock_collections.get(args.datablock_type)
    if collection is None:
        print(f"Error: Unsupported datablock type: {args.datablock_type}")
        sys.exit(1)
    
    # Track existing datablocks before append
    existing_datablocks = set(collection.keys())
    
    # Ensure source file path is absolute
    source_file = os.path.abspath(args.source_file)
    
    # Construct directory path inside the blend file
    source_dir = os.path.join(source_file, args.datablock_type)

    try:
        bpy.ops.wm.append(
            filepath=os.path.join(source_dir, args.datablock_name),
            directory=source_dir,
            filename=args.datablock_name,
            autoselect=True
        )
    except Exception as e:
        print(f"Failed to append: {e}")
        sys.exit(1)

    # Find the newly appended datablock
    new_datablocks = set(collection.keys()) - existing_datablocks
    
    if not new_datablocks:
        print(f"Error: No new datablock was appended. '{args.datablock_name}' may already exist in target.")
        sys.exit(1)
    
    # Get the actual name that was assigned (should only be one new datablock)
    actual_name = list(new_datablocks)[0]
    asset = collection[actual_name]
    
    if actual_name != args.datablock_name:
        print(f"Note: Datablock was renamed from '{args.datablock_name}' to '{actual_name}' due to name collision")

    # 3. Mark as Asset
    if asset:
        if args.append_only:
             print(f"Appended '{asset.name}'. Skipping asset marking (Append Only mode).")
             
             # Make Single User (specifically for Objects)
             if args.datablock_type == "Object":
                 try:
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
            try:
                asset.asset_generate_preview()
                print(f"Preview generated for '{asset.name}'")
            except Exception as e:
                print(f"Preview generation warning: {e}")
    else:
        print(f"Error: Could not find appended asset.")
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