#here is apis/info_api.py

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

import logging
logger = logging.getLogger(__name__)

import impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from models.extra_models import TokenModel  # noqa: F401
from models.info_models_get200_response import InfoModelsGet200Response
from models.info_models_get500_response import InfoModelsGet500Response


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/info/models",
    responses={
        200: {"model": InfoModelsGet200Response, "description": "Successful response with model data."},
        500: {"model": InfoModelsGet500Response, "description": "Internal Server Error"},
    },
    tags=["info"],
    summary="Retrieve model data.",
    response_model_by_alias=True,
)
async def info_models_get():
    try:
        import yaml
        yaml_file_path = "assets/model_info.yaml"
        # Read and parse the YAML file
        with open(yaml_file_path, 'r') as file:
            models_data = yaml.safe_load(file)
        
        # Extract the models section from the YAML file
        models = models_data.get("models", {})
        defaults = models_data.get("defaults", {})

        # Prepare the response data
        response_data = {
            "models": list(models.keys()),
            "defaults": defaults
        }

        return response_data
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)  # Log the exception details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

