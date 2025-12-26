"""
Create a comprehensive example of execution simulation output
Shows what the frontend receives with full lineage data
"""
import json
from app.models.execution import (
    ExecutionSimulation, Stage, Task, Partition, Shuffle, Node, SimulationEvent
)

def create_example_simulation():
    """Manually create a complete execution simulation example"""

    # Create nodes (executors)
    nodes = [
        Node(id=0, name="Worker 1", cores=4, memory_gb=4.0, assigned_tasks=[0, 1, 10, 11]),
        Node(id=1, name="Worker 2", cores=4, memory_gb=4.0, assigned_tasks=[2, 3, 12, 13]),
        Node(id=2, name="Worker 3", cores=4, memory_gb=4.0, assigned_tasks=[4, 5, 14]),
        Node(id=3, name="Worker 4", cores=4, memory_gb=4.0, assigned_tasks=[6, 7, 8, 9]),
    ]

    # Stage 0: Scan + Filter (10 partitions)
    stage0_tasks = []
    for i in range(10):
        stage0_tasks.append(Task(
            id=i,
            partition_id=i,
            node_id=i % 4,
            core_id=i % 4,
            start_time=0.0,
            end_time=0.5,
            duration=0.5,
            status="completed"
        ))

    stage0 = Stage(
        id=0,
        name="Scan + Filter",
        operation_type="scan",
        start_time=0.0,
        end_time=0.5,
        tasks=stage0_tasks,
        dependencies=[],
        parallelism=10,
        status="completed"
    )

    # Stage 1: Aggregate (5 partitions after shuffle)
    stage1_tasks = []
    for i in range(5):
        stage1_tasks.append(Task(
            id=10 + i,
            partition_id=10 + i,
            node_id=i % 4,
            core_id=(i + 1) % 4,
            start_time=0.8,
            end_time=1.2,
            duration=0.4,
            status="completed"
        ))

    stage1 = Stage(
        id=1,
        name="HashAggregate",
        operation_type="aggregate",
        start_time=0.8,
        end_time=1.2,
        tasks=stage1_tasks,
        dependencies=[0],
        parallelism=5,
        status="completed"
    )

    stages = [stage0, stage1]

    # Create shuffle between stages with partition mapping
    partition_mapping = {
        # Each of 10 source partitions goes to all 5 destination partitions
        0: [10, 11, 12, 13, 14],
        1: [10, 11, 12, 13, 14],
        2: [10, 11, 12, 13, 14],
        3: [10, 11, 12, 13, 14],
        4: [10, 11, 12, 13, 14],
        5: [10, 11, 12, 13, 14],
        6: [10, 11, 12, 13, 14],
        7: [10, 11, 12, 13, 14],
        8: [10, 11, 12, 13, 14],
        9: [10, 11, 12, 13, 14],
    }

    shuffle = Shuffle(
        from_stage_id=0,
        to_stage_id=1,
        data_volume_mb=25.0,
        from_partitions=10,
        to_partitions=5,
        start_time=0.5,
        end_time=0.8,
        partition_mapping=partition_mapping
    )

    shuffles = [shuffle]

    # Create partitions with lineage
    partitions = []

    # Stage 0 partitions (source data)
    for i in range(10):
        partitions.append(Partition(
            id=i,
            size_mb=2.5,
            records_count=1000,
            data_preview=None,
            stage_id=0,
            parent_partitions=[],  # No parents (source data)
            child_partitions=[10, 11, 12, 13, 14]  # All go to all stage 1 partitions
        ))

    # Stage 1 partitions (aggregated data)
    for i in range(5):
        partitions.append(Partition(
            id=10 + i,
            size_mb=5.0,
            records_count=500,
            data_preview=None,
            stage_id=1,
            parent_partitions=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Receives from all stage 0 partitions
            child_partitions=[]  # Final stage
        ))

    # Create timeline events
    events = []

    # Stage 0 events
    events.append(SimulationEvent(time=0.0, event_type="stage_start", stage_id=0, details={"name": "Scan + Filter"}))
    for task in stage0_tasks:
        events.append(SimulationEvent(time=task.start_time, event_type="task_start", stage_id=0, task_id=task.id))
        events.append(SimulationEvent(time=task.end_time, event_type="task_end", stage_id=0, task_id=task.id))
    events.append(SimulationEvent(time=0.5, event_type="stage_end", stage_id=0))

    # Shuffle events
    events.append(SimulationEvent(time=0.5, event_type="shuffle_start", details={"from_stage": 0, "to_stage": 1}))
    events.append(SimulationEvent(time=0.8, event_type="shuffle_end", details={"from_stage": 0, "to_stage": 1}))

    # Stage 1 events
    events.append(SimulationEvent(time=0.8, event_type="stage_start", stage_id=1, details={"name": "HashAggregate"}))
    for task in stage1_tasks:
        events.append(SimulationEvent(time=task.start_time, event_type="task_start", stage_id=1, task_id=task.id))
        events.append(SimulationEvent(time=task.end_time, event_type="task_end", stage_id=1, task_id=task.id))
    events.append(SimulationEvent(time=1.2, event_type="stage_end", stage_id=1))

    # Create metrics
    metrics = {
        "total_stages": 2,
        "total_tasks": 15,
        "total_shuffles": 1,
        "avg_parallelism": 7.5,
    }

    # Create complete simulation
    simulation = ExecutionSimulation(
        total_duration=1.2,
        partition_count=15,
        node_count=4,
        cores_per_node=4,
        total_cores=16,
        stages=stages,
        partitions=partitions,
        shuffles=shuffles,
        nodes=nodes,
        events=events,
        metrics=metrics
    )

    return simulation

def save_example_output():
    """Generate and save example output"""

    simulation = create_example_simulation()

    # Convert to dict
    simulation_dict = simulation.model_dump()

    # Save to file
    output_file = '/Users/liamnguyen/Documents/0.Coding/spark-playground-web/backend/EXAMPLE_EXECUTION_OUTPUT.json'
    with open(output_file, 'w') as f:
        json.dump(simulation_dict, f, indent=2)

    print("=" * 80)
    print("✅ EXAMPLE EXECUTION SIMULATION OUTPUT")
    print("=" * 80)
    print(f"\nFile saved to: {output_file}\n")

    # Print summary
    print("📊 SIMULATION SUMMARY")
    print("-" * 80)
    print(f"Total Duration: {simulation.total_duration}s")
    print(f"Stages: {len(simulation.stages)}")
    print(f"Partitions: {len(simulation.partitions)}")
    print(f"Shuffles: {len(simulation.shuffles)}")
    print(f"Executors: {len(simulation.nodes)}")
    print(f"Total Cores: {simulation.total_cores}")
    print(f"Timeline Events: {len(simulation.events)}")

    # Print stages
    print("\n🏭 STAGES")
    print("-" * 80)
    for stage in simulation.stages:
        print(f"Stage {stage.id}: {stage.name} ({stage.operation_type})")
        print(f"  ├─ Tasks: {len(stage.tasks)}")
        print(f"  ├─ Parallelism: {stage.parallelism}")
        print(f"  ├─ Dependencies: {stage.dependencies}")
        print(f"  └─ Duration: {stage.start_time}s → {stage.end_time}s")

    # Print shuffle
    print("\n🔀 SHUFFLES")
    print("-" * 80)
    for shuffle in simulation.shuffles:
        print(f"Shuffle: Stage {shuffle.from_stage_id} → Stage {shuffle.to_stage_id}")
        print(f"  ├─ Data Volume: {shuffle.data_volume_mb}MB")
        print(f"  ├─ Redistribution: {shuffle.from_partitions} → {shuffle.to_partitions} partitions")
        print(f"  └─ Mapping: All-to-All (each source → all destinations)")
        print(f"      Example: P0 → {shuffle.partition_mapping[0]}")

    # Print partition lineage
    print("\n📦 PARTITION LINEAGE")
    print("-" * 80)

    print("\nStage 0 Partitions (Source):")
    for p in simulation.partitions[:3]:
        print(f"  Partition {p.id}:")
        print(f"    ├─ Size: {p.size_mb}MB, Records: {p.records_count}")
        print(f"    ├─ Parents: {p.parent_partitions} (empty = source)")
        print(f"    └─ Children: {p.child_partitions}")
    print(f"  ... +{len([p for p in simulation.partitions if p.stage_id == 0]) - 3} more partitions")

    print("\nStage 1 Partitions (After Shuffle):")
    stage1_parts = [p for p in simulation.partitions if p.stage_id == 1]
    for p in stage1_parts[:2]:
        print(f"  Partition {p.id}:")
        print(f"    ├─ Size: {p.size_mb}MB, Records: {p.records_count}")
        print(f"    ├─ Parents: {p.parent_partitions}")
        print(f"    └─ Children: {p.child_partitions} (empty = final)")
    print(f"  ... +{len(stage1_parts) - 2} more partitions")

    # Print executor assignments
    print("\n💻 EXECUTOR ASSIGNMENTS")
    print("-" * 80)
    for node in simulation.nodes:
        print(f"{node.name} ({node.cores} cores, {node.memory_gb}GB)")
        tasks = [t for stage in simulation.stages for t in stage.tasks if t.node_id == node.id]
        print(f"  └─ Processing {len(tasks)} tasks: {[f'T{t.id}(P{t.partition_id})' for t in tasks[:4]]}")

    print("\n" + "=" * 80)
    print("💡 KEY INSIGHTS FROM THIS OUTPUT:")
    print("=" * 80)
    print("1. PARTITION LINEAGE:")
    print("   - Stage 0 partitions (P0-P9) have NO parents (source data)")
    print("   - Stage 0 partitions have children: ALL Stage 1 partitions (P10-P14)")
    print("   - Stage 1 partitions (P10-P14) have parents: ALL Stage 0 partitions")
    print("   - This shows the SHUFFLE redistributes data from 10 → 5 partitions")
    print()
    print("2. SHUFFLE MAPPING:")
    print("   - partition_mapping shows which source goes to which destination")
    print("   - All-to-all pattern: each source partition sends to ALL destinations")
    print("   - This is typical for hash partitioning in groupBy/aggregate")
    print()
    print("3. EXECUTOR ASSIGNMENTS:")
    print("   - Each task has node_id and core_id")
    print("   - Shows which worker/core processes which partition")
    print("   - Frontend uses this to display partition-to-executor mapping")
    print()
    print("4. TIMELINE EVENTS:")
    print("   - Events drive the animation (task_start, task_end, shuffle_start, etc.)")
    print("   - Frontend uses currentTime to determine what to show")
    print("=" * 80)

    return output_file

if __name__ == "__main__":
    output_file = save_example_output()
    print(f"\n✅ Open {output_file} to see the complete JSON structure!")
