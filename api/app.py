from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import sys
import os
import pandas as pd

# Add the current directory to Python path to import from index.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main function from index.py
from index import batch_predict, load_models, predict_shark_habitat,predict_shark_presence
import au_predict
# Initialize FastAPI app
app = FastAPI(title="Shark Prediction API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):  # Default file
    points_per_polygon: int = 200
    prediction_date: str = "2030-05-14"
    point_generation_method: str = "adaptive"  # 'random', 'grid', or 'adaptive'
    epsilon: float = 1.0  # DBSCAN parameter
    min_samples: int = 5  # DBSCAN parameter

class PredictionResponse(BaseModel):
    success: bool
    message: str
    presence_geojson_data: Optional[dict] = None
    habitat_geojson_data: Optional[dict] = None
    prediction_stats: Optional[dict] = None

@app.on_event("startup")
async def warm_up_predictor():
    """Load the Australia predictor (climatology, forecast, models) once at boot instead
    of on the first user request."""
    au_predict.get_predictor()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Shark Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        models = load_models()
        return {
            "status": "healthy", 
            "models_loaded": list(models.keys()),
            "available_models": ["sst", "ssh", "chla", "shark"]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Models not loaded: {str(e)}")

@app.get("/predict/presence")
async def shark_presence(date:str):
    """
    Main prediction endpoint: general shark presence zones around the Australian
    coastline, returned as a GeoJSON feature collection for frontend visualization
    """
    try:
        geojson_data = au_predict.predict_presence_geojson(date)
        if geojson_data:
            # Handle tuple return (presence, habitat) or single return
            
            return PredictionResponse(
                success=True,
                message="Clusters found",
                presence_geojson_data=geojson_data,
                prediction_stats=None
            )
            
        else:
            return PredictionResponse(
                success=False,
                message="No valid clusters found. Try adjusting parameters.",
                presence_geojson_data=None,
                habitat_geojson_data=None,
                prediction_stats=None
            )
           
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
@app.get("/predict/habitat")
async def shark_habitat(date:str, shark_name:str):
    """
    Species-specific habitat zones around the Australian coastline, returned as a
    GeoJSON feature collection for frontend visualization
    """
    try:
        geojson_data = au_predict.predict_habitat_geojson(date, shark_name)

        if geojson_data:
            # Handle tuple return (presence, habitat) or single return
            
            return PredictionResponse(
                success=True,
                message="No valid clusters found. Try adjusting parameters.",
                presence_geojson_data=None,
                habitat_geojson_data=geojson_data,
                prediction_stats=None
            )
        else:
            return PredictionResponse(
                success=False,
                message="No valid clusters found. Try adjusting parameters.",
                presence_geojson_data=None,
                habitat_geojson_data=None,
                prediction_stats=None
            )
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/predict/location")
async def location_predict(lat: float, lon: float, date: str = "2030-05-14"):
    """
    Simple prediction endpoint for single point prediction (Australian waters only:
    110-160E / 9-46S)
    """
    try:
        payload, error = au_predict.predict_location(lat, lon, date)
        if error:
            raise HTTPException(status_code=400, detail=error)
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simple prediction failed: {str(e)}")
class Question(BaseModel):
    context: list[str]
    question: str

# Global variable for lazy loading
rag_chain = None

def get_rag_chain():
    global rag_chain
    if rag_chain is None:
        try:
            rag_chain = build_rag_chain()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"RAG chain initialization failed: {str(e)}")
    return rag_chain


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
