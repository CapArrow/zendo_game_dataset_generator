import multiprocessing
import os
import yaml
from types import SimpleNamespace
from pipeline import generate_full_scene


def worker_process(scene_index, args):
    """
    Worker function that generates one scene.
    """
    success = generate_full_scene(args, scene_index)
    return (scene_index, success)


def main():
    # Load config file
    with open("configs/simple_config.yml") as f:
        args = yaml.safe_load(f)
    args = SimpleNamespace(**args)

    num_scenes = args.num_rules  # how many scenes to generate
    num_processes = min(multiprocessing.cpu_count(), num_scenes)

    print(f"🧠 Starting parallel generation using {num_processes} processes...")

    # Use a process pool
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Prepare arguments (scene indices)
        jobs = [(i, args) for i in range(num_scenes)]
        results = pool.starmap(worker_process, jobs)

    # Show summary
    success_count = sum(1 for _, success in results if success)
    print(f"\n✅ Done: {success_count}/{num_scenes} scenes generated successfully.")


if __name__ == "__main__":
    main()
