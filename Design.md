# Design.md  
## Requirements  
__Must have__:   
Moive CRUD, TMDB Lookup, Cover Images, Moive Details  
__Nice to have__:  
Recommendations for Tonight Moive, Ratings and Reviews  
## Data Models  
__User__ :  
- 'id' : Integer
- 'name' : String
- 'password' : String  

__Moive__ :
- 'id' : Primary key
- 'tmdb_id' : Moive ID from TMDB
- 'title' : String
- 'overview' : Text
- 'release_date' : Release date
- 'genres' : Moive genres  

__UserMoive__ :  
- 'id' : Primary key
- 'user_id' : Integer
- 'moive_id' : Integer
- 'statu' : String
- 'rating' : Float
- 'review' : Text
- 'created_at' : DateTime
## API Endpoints  
## MCP Server Plan
A MCP tool that let Cluade to search for database
## File Structure  
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
