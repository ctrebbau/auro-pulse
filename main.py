import uvicorn
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from vehicle_dashboard import app as vehicledash



app = FastAPI()
# Mount the Dash app as a sub-application in the FastAPI server
app.mount("/vehicledash", WSGIMiddleware(vehicledash.server))


# Define the main API endpoint
@app.get("/")
def index():
    return "Hello"


# Start the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")