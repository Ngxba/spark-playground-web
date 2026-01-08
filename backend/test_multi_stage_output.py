"""
Test script to generate multi-stage execution with shuffles
Shows complete partition lineage and shuffle mappings
"""
import json
from app.services.execution_simulator import ExecutionSimulator

def generate_multi_stage_output():
    """Generate multi-stage execution simulation with shuffles"""

    simulator = ExecutionSimulator()

    # Multi-stage physical plan with explicit shuffles
    physical_plan = """
    == Physical Plan ==
    AdaptiveSparkPlan isFinalPlan=false
    +- Project [category#12, sum#45L]
       +- SortAggregate(key=[category#12], functions=[sum(price#34)])
          +- Sort [category#12 ASC NULLS FIRST], false, 0
             +- Exchange hashpartitioning(category#12, 5), ENSURE_REQUIREMENTS, [id=#89]
                +- SortAggregate(key=[category#12], functions=[partial_sum(price#34)])
                   +- Project [category#12, price#34]
                      +- Filter (isnotnull(price#34) AND (price#34 > 10.0))
                         +- FileScan parquet [category#12, price#34]
                            Batched: true
                            Location: InMemoryFileIndex[file:///data/products.parquet]
                            ReadSchema: struct<category:string,price:double>
    """

    logical_plan = """
    == Analyzed Logical Plan ==
    category: string, sum: double
    Aggregate [category#12], [category#12, sum(price#34) AS sum#45L]
    +- Filter (price#34 > 10.0)
       +- Relation[category#12, price#34] parquet
    """

    # This should create stages info with shuffle
    execution_metadata = {
        "stages": 2,
        "has_shuffle": True,
    }

    # Generate simulation
    simulation = simulator.generate_simulation(
        physical_plan=physical_plan,
        logical_plan=logical_plan,
        execution_metadata=execution_metadata
    )

    if simulation:
        # Convert to dict for JSON serialization
        simulation_dict = simulation.model_dump()

        # Save to file with pretty formatting
        output_file = '/Users/liamnguyen/Documents/0.Coding/spark-playground-web/backend/multi_stage_execution_output.json'
        with open(output_file, 'w') as f:
            json.dump(simulation_dict, f, indent=2)

        print(f"✅ Multi-stage execution simulation saved to: {output_file}")
        print(f"\n📊 Summary:")
        print(f"  - Total Duration: {simulation.total_duration:.2f}s")
        print(f"  - Stages: {len(simulation.stages)}")
        print(f"  - Partitions: {len(simulation.partitions)}")
        print(f"  - Shuffles: {len(simulation.shuffles)}")
        print(f"  - Nodes: {len(simulation.nodes)}")
        print(f"  - Events: {len(simulation.events)}")

        # Print stage details
        print(f"\n🏭 Stages:")
        for stage in simulation.stages:
            print(f"  Stage {stage.id}: {stage.name}")
            print(f"    - Operation: {stage.operation_type}")
            print(f"    - Tasks: {len(stage.tasks)}")
            print(f"    - Parallelism: {stage.parallelism}")
            print(f"    - Dependencies: {stage.dependencies}")

        # Print partition lineage info (show more for multi-stage)
        print(f"\n📦 Partition Lineage (sample):")
        partitions_by_stage = {}
        for partition in simulation.partitions:
            if partition.stage_id not in partitions_by_stage:
                partitions_by_stage[partition.stage_id] = []
            partitions_by_stage[partition.stage_id].append(partition)

        for stage_id, parts in partitions_by_stage.items():
            print(f"\n  Stage {stage_id} Partitions:")
            for partition in parts[:3]:  # Show first 3 per stage
                print(f"    Partition {partition.id}:")
                print(f"      - Size: {partition.size_mb}MB, Records: {partition.records_count}")
                if partition.parent_partitions:
                    print(f"      - Parents: {partition.parent_partitions}")
                if partition.child_partitions:
                    print(f"      - Children: {partition.child_partitions}")

        # Print shuffle mapping info
        print(f"\n🔀 Shuffle Details:")
        for shuffle in simulation.shuffles:
            print(f"\n  Shuffle: Stage {shuffle.from_stage_id} → Stage {shuffle.to_stage_id}")
            print(f"    - Data Volume: {shuffle.data_volume_mb:.1f}MB")
            print(f"    - Redistribution: {shuffle.from_partitions} → {shuffle.to_partitions} partitions")
            print(f"    - Duration: {shuffle.start_time:.2f}s → {shuffle.end_time:.2f}s")

            # Show partition mapping
            if shuffle.partition_mapping:
                print(f"    - Partition Mapping (first 3):")
                for source_id, dest_ids in list(shuffle.partition_mapping.items())[:3]:
                    print(f"      P{source_id} → {['P'+str(d) for d in dest_ids]}")

        # Print task to partition assignments
        print(f"\n💻 Task Assignments (sample):")
        for stage in simulation.stages[:2]:  # First 2 stages
            print(f"\n  Stage {stage.id} Tasks:")
            for task in stage.tasks[:3]:  # First 3 tasks
                node = next((n for n in simulation.nodes if n.id == task.node_id), None)
                print(f"    Task {task.id}:")
                print(f"      - Partition: P{task.partition_id}")
                print(f"      - Executor: {node.name if node else 'Unknown'}, Core {task.core_id}")
                print(f"      - Duration: {task.duration:.2f}s ({task.start_time:.2f}s → {task.end_time:.2f}s)")

        return output_file
    else:
        print("❌ Failed to generate simulation")
        return None

if __name__ == "__main__":
    output_file = generate_multi_stage_output()
    if output_file:
        print(f"\n✅ Complete data structure saved to:")
        print(f"   {output_file}")
        print(f"\n💡 You can now examine:")
        print(f"   - Partition lineage (parent/child relationships)")
        print(f"   - Shuffle mappings (which partitions go where)")
        print(f"   - Task-to-executor assignments")
        print(f"   - Timeline events for animation")
