from app.models import Puzzle, Difficulty, ConceptTag

# Puzzle 1: Group the Fruits
PUZZLE_GROUP_FRUITS = Puzzle(
    id="group_fruits",
    title="Group the Fruits",
    description="Rearrange mixed fruits into organized groups",
    difficulty=Difficulty.EASY,
    tags=[ConceptTag.GROUPBY, ConceptTag.SHUFFLE, ConceptTag.PARTITIONING],
    scenario="""The factory has three conveyor belts carrying a mix of fruit items (apples, bananas, cherries).
The fruits are randomly distributed across the belts. Your task is to group the same fruits together into their
respective bins.""",
    goal="Group all fruits by their type so that each type is collected together.",
    initial_data={
        "fruits": [
            {"id": 1, "type": "apple", "color": "red"},
            {"id": 2, "type": "banana", "color": "yellow"},
            {"id": 3, "type": "apple", "color": "red"},
            {"id": 4, "type": "cherry", "color": "purple"},
            {"id": 5, "type": "banana", "color": "yellow"},
            {"id": 6, "type": "cherry", "color": "purple"},
            {"id": 7, "type": "apple", "color": "red"},
            {"id": 8, "type": "banana", "color": "yellow"},
            {"id": 9, "type": "cherry", "color": "purple"},
        ]
    },
    expected_output=[
        {"id": 1, "type": "apple", "color": "red"},
        {"id": 3, "type": "apple", "color": "red"},
        {"id": 7, "type": "apple", "color": "red"},
        {"id": 2, "type": "banana", "color": "yellow"},
        {"id": 5, "type": "banana", "color": "yellow"},
        {"id": 8, "type": "banana", "color": "yellow"},
        {"id": 4, "type": "cherry", "color": "purple"},
        {"id": 6, "type": "cherry", "color": "purple"},
        {"id": 9, "type": "cherry", "color": "purple"},
    ],
    starter_code="""# Group the fruits by type using PySpark
# The input DataFrame is called 'fruits'
# Store your result in a variable called 'result'
# Don't forget to call .show() or .collect() to see results!

result = fruits.orderBy('type')
result.show()
""",
    optimal_solution="""result = fruits.orderBy('type')
result.show()""",
    visualization_config={
        "input_conveyors": 3,
        "transformation": "sort",
        "output_conveyors": 3
    }
)

# Puzzle 2: Fast Join - Enrich Orders with Cities
PUZZLE_FAST_JOIN = Puzzle(
    id="fast_join",
    title="Fast Join - Enrich Orders with Cities",
    description="Join a large orders dataset with a small cities dataset efficiently",
    difficulty=Difficulty.MEDIUM,
    tags=[ConceptTag.JOIN, ConceptTag.BROADCAST, ConceptTag.OPTIMIZATION],
    scenario="""The factory has two conveyor belts: one with many Order boxes (with city codes), and another
with a few City Info boxes (city code and city name). You need to enrich each order with its city name.""",
    goal="Join the orders with city information efficiently. The cities dataset is much smaller than orders - use broadcast!",
    initial_data={
        "orders": [
            {"order_id": 1, "city_code": "NYC", "amount": 100},
            {"order_id": 2, "city_code": "LA", "amount": 200},
            {"order_id": 3, "city_code": "NYC", "amount": 150},
            {"order_id": 4, "city_code": "SF", "amount": 300},
            {"order_id": 5, "city_code": "LA", "amount": 250},
            {"order_id": 6, "city_code": "NYC", "amount": 180},
            {"order_id": 7, "city_code": "SF", "amount": 220},
            {"order_id": 8, "city_code": "LA", "amount": 190},
        ],
        "cities": [
            {"city_code": "NYC", "city_name": "New York"},
            {"city_code": "LA", "city_name": "Los Angeles"},
            {"city_code": "SF", "city_name": "San Francisco"},
        ]
    },
    expected_output=[
        {"order_id": 1, "city_code": "NYC", "amount": 100, "city_name": "New York"},
        {"order_id": 2, "city_code": "LA", "amount": 200, "city_name": "Los Angeles"},
        {"order_id": 3, "city_code": "NYC", "amount": 150, "city_name": "New York"},
        {"order_id": 4, "city_code": "SF", "amount": 300, "city_name": "San Francisco"},
        {"order_id": 5, "city_code": "LA", "amount": 250, "city_name": "Los Angeles"},
        {"order_id": 6, "city_code": "NYC", "amount": 180, "city_name": "New York"},
        {"order_id": 7, "city_code": "SF", "amount": 220, "city_name": "San Francisco"},
        {"order_id": 8, "city_code": "LA", "amount": 190, "city_name": "Los Angeles"},
    ],
    starter_code="""# Join orders with city information using PySpark
# Hint: cities is a small dataset - use broadcast() to avoid shuffle!
# Input DataFrames: 'orders' and 'cities'
# Store your result in 'result'

# Inefficient: regular join (causes shuffle)
result = orders.join(cities, 'city_code')
result.show()
""",
    optimal_solution="""# Optimal: Use broadcast join to avoid shuffle
from pyspark.sql.functions import broadcast
result = orders.join(broadcast(cities), 'city_code')
result.show()
""",
    visualization_config={
        "input_conveyors": 2,
        "transformation": "join",
        "output_conveyors": 1,
        "broadcast_eligible": True
    }
)

# Puzzle 3: Total Factory Output
PUZZLE_TOTAL_OUTPUT = Puzzle(
    id="total_output",
    title="Total Factory Output",
    description="Calculate total quantities by product type",
    difficulty=Difficulty.EASY,
    tags=[ConceptTag.AGGREGATION, ConceptTag.GROUPBY, ConceptTag.SHUFFLE],
    scenario="""The factory conveyor carries products with types and quantities. The boss wants to see
the total quantity of products by type.""",
    goal="Aggregate the products to show total quantity per product type.",
    initial_data={
        "products": [
            {"type": "A", "quantity": 10},
            {"type": "B", "quantity": 5},
            {"type": "A", "quantity": 20},
            {"type": "C", "quantity": 15},
            {"type": "B", "quantity": 10},
            {"type": "A", "quantity": 30},
            {"type": "C", "quantity": 5},
            {"type": "B", "quantity": 15},
        ]
    },
    expected_output=[
        {"type": "A", "quantity": 60},
        {"type": "B", "quantity": 30},
        {"type": "C", "quantity": 20},
    ],
    starter_code="""# Calculate total quantity per product type using PySpark
# Input DataFrame: 'products'
# Store your result in 'result'

from pyspark.sql.functions import sum

result = products.groupBy('type').agg(sum('quantity').alias('quantity'))
result.show()
""",
    optimal_solution="""from pyspark.sql.functions import sum
result = products.groupBy('type').agg(sum('quantity').alias('quantity'))
result.show()""",
    visualization_config={
        "input_conveyors": 1,
        "transformation": "aggregate",
        "output_conveyors": 1
    }
)

# Puzzle 4: Filter Before Merge
PUZZLE_FILTER_MERGE = Puzzle(
    id="filter_merge",
    title="Filter Before Merge",
    description="Remove defective items before joining with additional info",
    difficulty=Difficulty.MEDIUM,
    tags=[ConceptTag.FILTER, ConceptTag.JOIN, ConceptTag.OPTIMIZATION],
    scenario="""The factory has a conveyor of items, some marked as defective. These items will be joined
with additional information. Defective items should NOT be processed at all.""",
    goal="Remove defective products BEFORE joining with info to avoid wasting processing power.",
    initial_data={
        "items": [
            {"item_id": 1, "defective": False, "info_key": "A"},
            {"item_id": 2, "defective": True, "info_key": "B"},
            {"item_id": 3, "defective": False, "info_key": "A"},
            {"item_id": 4, "defective": False, "info_key": "C"},
            {"item_id": 5, "defective": True, "info_key": "B"},
            {"item_id": 6, "defective": False, "info_key": "C"},
        ],
        "info": [
            {"info_key": "A", "category": "Electronics"},
            {"info_key": "B", "category": "Furniture"},
            {"info_key": "C", "category": "Clothing"},
        ]
    },
    expected_output=[
        {"item_id": 1, "defective": False, "info_key": "A", "category": "Electronics"},
        {"item_id": 3, "defective": False, "info_key": "A", "category": "Electronics"},
        {"item_id": 4, "defective": False, "info_key": "C", "category": "Clothing"},
        {"item_id": 6, "defective": False, "info_key": "C", "category": "Clothing"},
    ],
    starter_code="""# Join items with info, but only for non-defective items
# Think about WHEN to filter for best performance!
# Input DataFrames: 'items' and 'info'
# Store your result in 'result'

from pyspark.sql.functions import col

# Inefficient: filter after join
result = items.join(info, 'info_key')
result = result.filter(col('defective') == False)
result.show()
""",
    optimal_solution="""# Optimal: filter before join (pushdown optimization)
from pyspark.sql.functions import col
clean_items = items.filter(col('defective') == False)
result = clean_items.join(info, 'info_key')
result.show()
""",
    visualization_config={
        "input_conveyors": 2,
        "transformation": "filter_then_join",
        "output_conveyors": 1
    }
)

# Puzzle 5: Cache or Not to Cache
PUZZLE_CACHE = Puzzle(
    id="cache_puzzle",
    title="Cache or Not to Cache",
    description="Optimize repeated dataset access with caching",
    difficulty=Difficulty.HARD,
    tags=[ConceptTag.CACHE, ConceptTag.OPTIMIZATION],
    scenario="""The factory processes the same raw materials twice: once to count items and once to
filter and prepare for shipping. Currently, it's reading the data twice.""",
    goal="Use caching to store intermediate results and avoid reprocessing the same data.",
    initial_data={
        "raw_materials": [
            {"id": 1, "material": "steel", "weight": 100},
            {"id": 2, "material": "wood", "weight": 50},
            {"id": 3, "material": "steel", "weight": 150},
            {"id": 4, "material": "plastic", "weight": 30},
            {"id": 5, "material": "wood", "weight": 70},
            {"id": 6, "material": "steel", "weight": 120},
        ]
    },
    expected_output={
        "counts": [
            {"material": "plastic", "count": 1},
            {"material": "steel", "count": 3},
            {"material": "wood", "count": 2},
        ],
        "heavy_items": [
            {"id": 1, "material": "steel", "weight": 100},
            {"id": 3, "material": "steel", "weight": 150},
            {"id": 5, "material": "wood", "weight": 70},
            {"id": 6, "material": "steel", "weight": 120},
        ]
    },
    starter_code="""# Process the data twice: count by material and filter heavy items
# Currently inefficient - data is processed twice without caching
# Input DataFrame: 'raw_materials'
# Store counts and heavy items, then return as dict

from pyspark.sql.functions import col, count as spark_count

# First usage: count (without cache - inefficient!)
counts = raw_materials.groupBy('material').agg(spark_count('*').alias('count'))

# Second usage: filter (reprocesses the same data!)
heavy_items = raw_materials.filter(col('weight') >= 70)

# Collect results
counts_data = counts.collect()
heavy_data = heavy_items.collect()

# Convert to dict format
result = {
    'counts': [row.asDict() for row in counts_data],
    'heavy_items': [row.asDict() for row in heavy_data]
}
""",
    optimal_solution="""# Optimal: Use .cache() to store intermediate results
from pyspark.sql.functions import col, count as spark_count

# Cache the DataFrame since we'll use it twice
cached_data = raw_materials.cache()

# First usage: count
counts = cached_data.groupBy('material').agg(spark_count('*').alias('count'))

# Second usage: filter (uses cached data - efficient!)
heavy_items = cached_data.filter(col('weight') >= 70)

# Collect results
counts_data = counts.collect()
heavy_data = heavy_items.collect()

# Convert to dict format
result = {
    'counts': [row.asDict() for row in counts_data],
    'heavy_items': [row.asDict() for row in heavy_data]
}
""",
    visualization_config={
        "input_conveyors": 1,
        "transformation": "multi_use",
        "output_conveyors": 2,
        "cache_point": True
    }
)

# All puzzles registry
ALL_PUZZLES = [
    PUZZLE_GROUP_FRUITS,
    PUZZLE_FAST_JOIN,
    PUZZLE_TOTAL_OUTPUT,
    PUZZLE_FILTER_MERGE,
    PUZZLE_CACHE,
]
