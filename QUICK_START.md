# Quick Start Guide

## What Was Built

You now have a complete Phase 1 MVP of the Spark Playground web application with:

### Backend (FastAPI)
- ✅ Full FastAPI project structure
- ✅ 5 puzzle definitions (Group Fruits, Fast Join, Total Output, Filter Before Merge, Cache Puzzle)
- ✅ Code execution sandbox using Pandas
- ✅ Operation detector to analyze Spark patterns in code
- ✅ Metrics simulator for shuffles, stages, and performance
- ✅ Correctness checker with output comparison
- ✅ Hint generator with puzzle-specific suggestions
- ✅ RESTful API endpoints for puzzles and code execution
- ✅ Dockerfile for containerization

### Frontend (React + Vite)
- ✅ Modern React application with Vite
- ✅ Puzzle Selection page with difficulty badges and tags
- ✅ Puzzle Workspace with split-screen layout
- ✅ Monaco Editor integration (VS Code engine)
- ✅ Simplified Factory Visualization with SVG animations
- ✅ Run Report modal with metrics and star ratings
- ✅ Full API integration with backend
- ✅ Responsive design and professional styling
- ✅ Dockerfile for containerization

### Infrastructure
- ✅ Docker Compose for easy deployment
- ✅ Comprehensive README with documentation
- ✅ Complete project structure

## How to Run

### Option 1: Docker Compose (Recommended)

```bash
# Start both frontend and backend
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Run Locally

#### Terminal 1 - Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173 in your browser.

## Testing the Application

### 1. Test Backend API

```bash
# Get all puzzles
curl http://localhost:8000/api/puzzles

# Get a specific puzzle
curl http://localhost:8000/api/puzzles/group_fruits

# Test code execution
curl -X POST http://localhost:8000/api/puzzles/group_fruits/run \
  -H "Content-Type: application/json" \
  -d '{"code": "result = fruits.sort_values(\"type\")"}'
```

### 2. Test Frontend

1. Open http://localhost:5173
2. You should see 5 puzzle cards
3. Click on "Group the Fruits" (Easy puzzle)
4. Try running the starter code
5. Observe the factory animation
6. Check the Run Report with metrics and star rating

### 3. Test Different Solutions

#### Puzzle 1: Group the Fruits

**Optimal Solution (3 stars):**
```python
result = fruits.sort_values('type')
```

**Alternative (also works):**
```python
result = fruits.groupby('type').apply(lambda x: x).reset_index(drop=True)
```

#### Puzzle 2: Fast Join

**Optimal Solution (3 stars with broadcast):**
```python
cities_broadcast = cities.drop_duplicates()
result = orders.merge(cities_broadcast, on='city_code')
```

**Suboptimal (2 stars - missing broadcast hint):**
```python
result = orders.merge(cities, on='city_code')
```

#### Puzzle 3: Total Output

**Optimal Solution (3 stars):**
```python
result = products.groupby('type')['quantity'].sum().reset_index()
```

#### Puzzle 4: Filter Before Merge

**Optimal Solution (3 stars - filter first):**
```python
clean_items = items[items['defective'] == False]
result = clean_items.merge(info, on='info_key')
```

**Suboptimal (2 stars - filter after):**
```python
result = items.merge(info, on='info_key')
result = result[result['defective'] == False]
```

#### Puzzle 5: Cache or Not to Cache

**Optimal Solution (3 stars - uses caching):**
```python
data = raw_materials.copy()  # Simulate cache
counts = data.groupby('material').size().reset_index(name='count')
heavy_items = data[data['weight'] >= 70]
result = {'counts': counts.to_dict('records'), 'heavy_items': heavy_items.to_dict('records')}
```

## Features to Explore

1. **Visual Factory Animation**: Watch boxes move through the factory as your code runs
2. **Performance Metrics**: See shuffle count, stages, and execution time
3. **Star Ratings**: Get 1-3 stars based on solution efficiency
4. **Hints System**: Receive context-aware hints for optimization
5. **Error Handling**: Clear error messages for syntax or runtime errors
6. **Difficulty Levels**: Progress from Easy to Hard puzzles

## Project Structure Overview

```
backend/
  app/
    api/puzzles.py         # API endpoints
    models/                # Pydantic models
    services/
      executor.py          # Code execution sandbox
      operation_detector.py # Analyzes code for Spark patterns
      metrics_calculator.py # Simulates performance metrics
      hint_generator.py    # Generates optimization hints
      judge.py            # Main judging system
    puzzles/
      puzzle_definitions.py # All 5 puzzle definitions

frontend/
  src/
    pages/
      PuzzleList.jsx       # Home page with puzzle grid
      PuzzleWorkspace.jsx  # Main coding interface
    components/
      FactoryVisualization.jsx # SVG-based factory animation
      RunReport.jsx        # Results modal
    services/
      api.js              # Backend API client
```

## Next Steps

1. **Start the application** using one of the methods above
2. **Solve all 5 puzzles** to understand the concepts
3. **Experiment** with different solutions to see how metrics change
4. **Customize** puzzles or add new ones in `puzzle_definitions.py`
5. **Enhance visualizations** in `FactoryVisualization.jsx`

## Troubleshooting

### Backend Issues
- Make sure Python 3.11+ is installed
- Check that port 8000 is not in use
- Verify all dependencies installed: `pip install -r requirements.txt`

### Frontend Issues
- Make sure Node.js 18+ is installed
- Check that port 5173 is not in use
- Clear cache: `rm -rf node_modules && npm install`
- Check API URL in `.env`: `VITE_API_URL=http://localhost:8000/api`

### Docker Issues
- Ensure Docker Desktop is running
- Try: `docker-compose down && docker-compose up --build`
- Check logs: `docker-compose logs backend` or `docker-compose logs frontend`

## What's Next? (Phase 2 Ideas)

- Add user authentication and progress tracking
- Create 15-20 more puzzles
- Implement real PySpark execution option
- Add leaderboards and challenges
- More advanced visualizations
- Window functions and UDF puzzles
- Streaming data puzzles

Enjoy learning Spark! 🎉
