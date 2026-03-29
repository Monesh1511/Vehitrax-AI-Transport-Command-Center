import uvicorn
import os

if __name__ == "__main__":
    print("Starting Vehitrax AI Backend Server...")
    # Ensures the current working directory is the backend folder before starting 
    # so that imports inside your codebase resolve properly.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
