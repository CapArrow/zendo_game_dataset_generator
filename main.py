import multiprocessing
import os
import time

import yaml
from types import SimpleNamespace
from pipeline import generate_full_scene
from render_batch import render_scene_from_blend


def worker_process(scene_index, args):
    success = generate_full_scene(args, scene_index)
    return (scene_index, success)


def run_generation(args):
    num_scenes = args.num_rules
    num_processes = min(multiprocessing.cpu_count(), num_scenes)

    print(f"\n🚀 Generating {num_scenes} scenes using {num_processes} processes...\n")

    with multiprocessing.Pool(processes=num_processes) as pool:
        jobs = [(i, args) for i in range(num_scenes)]
        results = pool.starmap(worker_process, jobs)
        pool.close()
        pool.join()

    success_count = sum(1 for _, success in results if success)
    print(f"\n✅ Generation done: {success_count}/{num_scenes} scenes succeeded.\n")

    expected_blend_files = {f"scene_{i}.blend" for i in range(args.num_rules)}
    actual_blend_files = set()

    while actual_blend_files != expected_blend_files:
        actual_blend_files = set(f for f in os.listdir(args.output_dir) if f.endswith(".blend"))
        time.sleep(0.5)  # wait a bit before checking again


def run_rendering(args):
    print(f"\n🎨 Starting rendering of saved scenes...\n")

    os.makedirs(args.output_dir, exist_ok=True)

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

    blend_files = sorted(f for f in os.listdir(args.output_dir) if f.endswith(".blend"))
    for i, blend_file in enumerate(blend_files):
        blend_path = os.path.join(args.output_dir, blend_file)
        render_scene_from_blend(args, blend_path, i)

    print(f"\n✅ Rendering complete.\n")


def main():
    with open("configs/simple_config.yml") as f:
        args_dict = yaml.safe_load(f)
    args = SimpleNamespace(**args_dict)

    run_generation(args)
    run_rendering(args)


if __name__ == "__main__":
    main()
