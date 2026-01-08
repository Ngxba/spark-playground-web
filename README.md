# Spark Playground

An interactive web application for learning Apache Spark through gamified puzzle challenges. Learn Spark concepts like joins, aggregations, shuffles, and performance optimization in a visual, hands-on environment.

## Features

- **Interactive Puzzles**: 5 carefully designed puzzles covering core Spark concepts
- **Visual Factory Metaphor**: See your Spark transformations come to life with animated visualizations
- **Real-time Feedback**: Get instant evaluation with correctness checking, performance metrics, and optimization hints
- **LeetCode-style Judging**: Earn stars based on code efficiency and best practices
- **In-browser Code Editor**: Monaco Editor (VS Code engine) with Python syntax highlighting
- **Performance Metrics**: Track shuffles, stages, execution time, and optimization opportunities

## Architecture

- **Frontend**: React + Vite, Monaco Editor, React Router
- **Backend**: FastAPI (Python), Pandas for execution, Custom Spark metrics simulator
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Or: Node.js 18+ and Python 3.11+ for local development

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd spark-playground-web
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

## Puzzles

### 1. Group the Fruits (Easy)
- **Concepts**: GroupBy, Partitioning, Shuffles
- **Goal**: Organize mixed fruits by type
- **Learn**: How partitioning and grouping operations work in Spark

### 2. Fast Join - Enrich Orders with Cities (Medium)
- **Concepts**: Joins, Broadcast Optimization
- **Goal**: Join large orders dataset with small cities reference data
- **Learn**: When and how to use broadcast joins for performance

### 3. Total Factory Output (Easy-Medium)
- **Concepts**: Aggregation, GroupBy
- **Goal**: Calculate total quantities by product type
- **Learn**: Aggregation patterns and their performance characteristics

### 4. Filter Before Merge (Medium)
- **Concepts**: Filter Pushdown, Operation Ordering
- **Goal**: Remove defective items before joining with additional info
- **Learn**: Why operation order matters for performance

### 5. Cache or Not to Cache (Hard)
- **Concepts**: Caching, Optimization
- **Goal**: Optimize repeated dataset access
- **Learn**: When caching improves performance vs. when it's unnecessary

## Project Structure

```
spark-playground-web/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models/        # Data models
│   │   ├── services/      # Business logic (executor, judge, metrics)
│   │   ├── puzzles/       # Puzzle definitions
│   │   └── main.py        # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── App.jsx        # Main app component
│   ├── Dockerfile
│   └── package.json
├── IMPLEMENTATION/        # Design docs
├── docker-compose.yml
└── README.md
```

## Development

### Backend Development

The backend uses:
- **FastAPI** for API endpoints
- **Pandas** for code execution on small datasets
- **Custom operation detector** to analyze code for Spark patterns
- **Metrics simulator** to estimate shuffle/stage counts and performance

To add a new puzzle:
1. Create puzzle definition in `backend/app/puzzles/puzzle_definitions.py`
2. Add optimal criteria in `Judge._get_optimal_criteria()`
3. Add puzzle-specific hints in `HintGenerator.generate_hint()`

### Frontend Development

The frontend uses:
- **React** with functional components and hooks
- **Monaco Editor** for code editing
- **SVG-based visualizations** for the factory view
- **Axios** for API communication

To customize visualizations:
1. Edit `FactoryVisualization.jsx` for animation logic
2. Modify CSS for styling and animation effects

## Testing

### Manual Testing

Test each puzzle with different solutions:

1. **Optimal solution** (should get 3 stars)
2. **Suboptimal but correct** (should get 2 stars)
3. **Incorrect solution** (should show error with hint)

### Backend API Testing

```bash
# Test puzzle list
curl http://localhost:8000/api/puzzles

# Test specific puzzle
curl http://localhost:8000/api/puzzles/group_fruits

# Test code execution
curl -X POST http://localhost:8000/api/puzzles/group_fruits/run \
  -H "Content-Type: application/json" \
  -d '{"code": "result = fruits.sort_values(\"type\")"}'
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Performance Metrics Explained

- **Time**: Simulated execution time based on operation costs
- **Shuffles**: Number of data shuffle operations (fewer is better)
- **Stages**: Number of Spark stages (fewer is better)
- **Broadcast**: Whether broadcast join optimization was used
- **Cache**: Whether data caching was utilized
- **Skew**: Whether data imbalance was detected

## Star Rating System

- **⭐⭐⭐ (3 stars)**: Optimal solution - correct and efficient
- **⭐⭐ (2 stars)**: Correct but could be optimized
- **⭐ (1 star)**: Works but inefficient
- **No stars**: Incorrect output or execution error

## Future Enhancements (Phase 2 & 3)

- User authentication and progress tracking
- More advanced puzzles (20+ total)
- Real-time collaboration features
- Leaderboards and challenges
- Additional Spark concepts (window functions, UDFs, etc.)
- Actual PySpark execution option
- More detailed performance profiling

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built as an educational tool to make learning Apache Spark more engaging and interactive.
