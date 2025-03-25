import json
import bpy
import sys
import os
import argparse
import yaml
from types import SimpleNamespace

from generate import generate_structure
from render import render, get_all_scene_objects
from zendo_objects import get_from_blender_obj, ZendoObject


def render_scene_from_blend(args, blend_path, scene_index):
    """
    Loads a .blend file, renders it, and logs metadata to ground_truth.csv
    """

    # Open the saved blend file
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    # Load rule, query, and structure from JSON
    json_path = blend_path.replace(".blend", ".json")
    with open(json_path, encoding='utf-8') as jf:
        meta = json.load(jf)
    rule = meta.get("rule", "N/A")
    query = meta.get("query", "N/A")
    structure = meta.get("structure", [])

    # Clear existing objects if needed
    ZendoObject.instances.clear()

    # Create a dummy collection to populate the scene with objects
    collection = bpy.data.collections.new("RenderCollection")
    bpy.context.scene.collection.children.link(collection)

    # Extract scene name from filename
    scene_name = f"scene_{scene_index}"
    output_img_name = scene_name + ".png"
    output_img_path = os.path.join(args.output_dir, output_img_name)

    # Render the scene
    render(args, "", scene_name)

    # Get all ZendoObjects in scene
    scene_objects = ZendoObject.instances

    # Write object metadata to CSV
    csv_path = os.path.join(args.output_dir, "ground_truth.csv")
    with open(csv_path, "a", newline="") as csvfile:
        import csv
        writer = csv.writer(csvfile)

        for obj in scene_objects:
            min_bb, max_bb = obj.get_world_bounding_box()
            pos = obj.get_position()

            writer.writerow([
                scene_name, output_img_path, rule, query, obj.name,
                min_bb.x, min_bb.y, min_bb.z,
                max_bb.x, max_bb.y, max_bb.z,
                pos.x, pos.y, pos.z
            ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config-file", type=str, default="configs/simple_config.yml")
    args_ns = parser.parse_args()

    # Load YAML config
    with open(args_ns.config_file) as f:
        args_dict = yaml.safe_load(f)
    args = SimpleNamespace(**args_dict)

    os.makedirs(args.output_dir, exist_ok=True)

    # Write CSV header
    csv_path = os.path.join(args.output_dir, "ground_truth.csv")
    with open(csv_path, "w", newline="") as csvfile:
        import csv
        writer = csv.writer(csvfile)
        writer.writerow([
            "scene_name", "img_path", "rule", "query", "object_name",
            "bounding_box_min_x", "bounding_box_min_y", "bounding_box_min_z",
            "bounding_box_max_x", "bounding_box_max_y", "bounding_box_max_z",
            "world_pos_x", "world_pos_y", "world_pos_z"
        ])

    # Get all .blend files
    blend_files = sorted(
        f for f in os.listdir(args.output_dir)
        if f.endswith(".blend")
    )

    for i, blend_file in enumerate(blend_files):
        blend_path = os.path.join(args.output_dir, blend_file)
        render_scene_from_blend(args, blend_path, i)


if __name__ == "__main__":
    main()
