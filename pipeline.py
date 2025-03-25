import json
import os
import bpy
from rules.rules import generate_rule, generate_prolog_structure
from generate import generate_structure
from zendo_objects import ZendoObject


def generate_full_scene(args, scene_index):
    """
    Generates a full Blender scene from rule to populated objects.
    Includes retry logic if structure placement fails.
    """

    # ✅ Load the base Blender scene (camera, ground, etc.)
    bpy.ops.wm.open_mainfile(filepath=args.base_scene_blendfile)

    for attempt in range(args.resolve_attempts):
        # Step 1: Generate a rule and Prolog query
        rule, query, _ = generate_rule(args.rules_json_file)

        # Step 2: Generate object structure from Prolog
        structures = generate_prolog_structure(1, query, args.rules_prolog_file)
        if not structures or len(structures) == 0:
            print(f"[Scene {scene_index}] Attempt {attempt+1}: Failed to generate structure")
            continue

        structure = structures[0]

        # Step 3: Create a new Blender collection for this scene
        collection = bpy.data.collections.new(f"Structure_{scene_index}")
        bpy.context.scene.collection.children.link(collection)

        # Step 4: Generate the Blender objects
        try:
            generate_structure(args, structure, collection)
            print(f"[Scene {scene_index}] Success on attempt {attempt+1}")


            # ✅ Save to .blend
            os.makedirs(args.output_dir, exist_ok=True)
            output_path = os.path.join(args.output_dir, f"scene_{scene_index}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=output_path)
            print(f"[Scene {scene_index}] Saved to {output_path}")

            json_path = os.path.join(args.output_dir, f"scene_{scene_index}.json")
            with open(json_path, 'w', encoding='utf-8') as f_json:
                json.dump({
                    "rule": rule,
                    "query": query,
                    "structure": structure
                }, f_json, indent=2)
            print(f"[Scene {scene_index}] Metadata saved to {json_path}")

            return True
        except Exception as e:
            print(f"[Scene {scene_index}] Attempt {attempt+1} failed: {e}")

            # Cleanup failed attempt
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)

            ZendoObject.instances.clear()
            continue

    # ❌ All attempts failed
    print(f"[Scene {scene_index}] All {args.resolve_attempts} attempts failed.")
    return False
