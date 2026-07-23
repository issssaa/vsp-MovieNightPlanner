# CLUADE.md
## Project Overview
A platform for users to search for movies, create personal movie lists, and mark movies as watched or planned to watch. It can also combine multiple users’ preferences to recommend a movie to watch together.

Current Stage: Design
## Architecture
framework: FastAPI  
Database: SQLite with SQLAlchemy  
External API: TMDB API  
Project structure:   
```
MovieNightPlanner/  
│    
├── app/   
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   ├── models/
│   └── schemas/
│
├── tests/
├── requirements.txt
├── README.md
├── DESIGN.md
└── CLAUDE.md
```
## How to run
```
pip install -r requirements.txt
```

## Code Conventions
models in `models/.`  
routers in `routers/.`  
API return JSON

## Common Tasks
