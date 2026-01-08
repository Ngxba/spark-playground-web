"""
Test script to generate execution simulation output and save to file
This helps visualize what data the backend generates for the frontend
"""
import json
from app.services.execution_simulator import ExecutionSimulator

def generate_sample_output():
    """Generate sample execution simulation and save to file"""

    simulator = ExecutionSimulator()

    # Sample physical plan (simulating a groupBy query)
    physical_plan = """
    == Physical Plan ==
    AdaptiveSparkPlan isFinalPlan=false
    +- HashAggregate(keys=[category#12], functions=[count(1)])
       +- Exchange hashpartitioning(category#12, 5), ENSURE_REQUIREMENTS, [id=#34]
          +- HashAggregate(keys=[category#12], functions=[partial_count(1)])
             +- FileScan parquet [category#12]
                Batched: true
                Location: InMemoryFileIndex[file:///data/products.parquet]
                ReadSchema: struct<category:string>
    """

    logical_plan = """
    == Analyzed Logical Plan ==
    category: string, count: bigint
    Aggregate [category#12], [category#12, count(1) AS count#25L]
    +- Relation[category#12] parquet
    """

    # Generate simulation
    simulation = simulator.generate_simulation(
        physical_plan=physical_plan,
        logical_plan=logical_plan,
        execution_metadata=None
    )

    if simulation:
        # Convert to dict for JSON serialization
        simulation_dict = simulation.model_dump()

        # Save to file with pretty formatting
        output_file = '/Users/liamnguyen/Documents/0.Coding/spark-playground-web/backend/sample_execution_output.json'
        with open(output_file, 'w') as f:
            json.dump(simulation_dict, f, indent=2)

        print(f"✅ Execution simulation saved to: {output_file}")
        print(f"\nSummary:")
        print(f"  - Total Duration: {simulation.total_duration:.2f}s")
        print(f"  - Stages: {len(simulation.stages)}")
        print(f"  - Partitions: {len(simulation.partitions)}")
        print(f"  - Shuffles: {len(simulation.shuffles)}")
        print(f"  - Nodes: {len(simulation.nodes)}")
        print(f"  - Events: {len(simulation.events)}")

        # Print partition lineage info
        print(f"\n📊 Partition Lineage:")
        for partition in simulation.partitions[:5]:  # Show first 5
            print(f"  Partition {partition.id}:")
            print(f"    - Stage: {partition.stage_id}")
            print(f"    - Parents: {partition.parent_partitions}")
            print(f"    - Children: {partition.child_partitions}")

        # Print shuffle mapping info
        print(f"\n🔀 Shuffle Mappings:")
        for shuffle in simulation.shuffles:
            print(f"  Shuffle: Stage {shuffle.from_stage_id} → Stage {shuffle.to_stage_id}")
            print(f"    - Data Volume: {shuffle.data_volume_mb}MB")
            print(f"    - From Partitions: {shuffle.from_partitions}")
            print(f"    - To Partitions: {shuffle.to_partitions}")
            print(f"    - Mapping Sample: {dict(list(shuffle.partition_mapping.items())[:3])}")

        return output_file
    else:
        print("❌ Failed to generate simulation")
        return None

if __name__ == "__main__":
    output_file = generate_sample_output()
    if output_file:
        print(f"\n✅ Open the file to examine the complete data structure:")
        print(f"   {output_file}")
