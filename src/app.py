# here is app.py

from indented_logger import setup_logging
import logging
from fastapi import Depends, Request

import os

log_file_path = os.path.expanduser("~/my_logs/app.log")
# log_file_path = "/var/log/my_app/app.log"

log_dir = os.path.dirname(log_file_path)
os.makedirs(log_dir, exist_ok=True)


setup_logging(level=logging.DEBUG,
            log_file=log_file_path, 
            include_func=True, 
            include_module=False, 
            no_datetime=True, 
            min_func_name_col=100 )


logging.getLogger("passlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

logger.debug("start")
import logging
from datetime import datetime






from fastapi import FastAPI
from core.dependencies import setup_dependencies


from apis.chat_api import router as ChatApiRouter
from apis.info_api import router as InfoApiRouter
from apis.auth_api import router as AuthApiRouter


from starlette.middleware.base import BaseHTTPMiddleware
import uuid

# from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware




# logging.getLogger("pdfplumber").setLevel(logging.WARNING)
# logging.getLogger("pdfminer").setLevel(logging.WARNING)
# logging.getLogger("fitz").setLevel(logging.WARNING)  # If usi




app = FastAPI(
     
    title="voice chat API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    description="API for voice chat",
    version="1.0.0",

)



origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:5174",
    "http://localhost:3000",
     "http://localhost:443",

]




class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate a new UUID for this request
        request_id = str(uuid.uuid4())
        
        # Optionally, add the request_id to headers for downstream usage
        # (e.g., logging or returning to the client)
        request.state.request_id = request_id

        # You can also add it as a header in the response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins , # Adjust this to more specific domains for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.add_middleware(RequestIDMiddleware)



# app.include_router(AdminPanelApiRouter)
app.include_router(AuthApiRouter)
app.include_router(ChatApiRouter)

app.include_router(InfoApiRouter)

# app.include_router(DependenciesApiRouter)

services = setup_dependencies()

@app.on_event("startup")
async def startup_event():
    app.state.services = services
    logger.debug("Configurations loaded and services initialized")



















# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Log format
# logger = logging.getLogger(__name__)
# from fastapi.middleware.cors import CORSMiddleware

# # pip install cloud-sql-python-connector[pymysql] SQLAlchemy==2.0.7



# # from apis.task_api import router as TaskApiRouter
# # from apis.user_api import router as UserApiRouter


# app = FastAPI(
#     title="FastAPI Application",
#     description="API for voice chat",
#     version="1.0.0",
# )

# # origins = [
# #     "http://localhost:5173",  # Add specific origins here
# #     "https://enes-talk-w-sql.vercel.app",
# #     "https://api.budgety.ai",
# #     "https://wwww.budgety.ai",
# #     "https://editor.swagger.io/"
# # ]


# origins = [
#     "http://localhost:5173",  # Add specific origins here
#     "http://localhost:5174",  # Add specific origins here
#     "https://enes-talk-w-sql.vercel.app",
#     "https://db-whisperer.vercel.app",
#     "https://api.budgety.ai",
#     "https://api.budgety.ai:3000",
#     "https://editor.swagger.io/" ,
#     "https://editor.swagger.io"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins , # Adjust this to more specific domains for security
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )


# app.include_router(ChatApiRouter)
# app.include_router(InfoApiRouter)
# app.include_router(TaskApiRouter)
# app.include_router(UserApiRouter)


# from fastapi.exceptions import RequestValidationError
# from fastapi.responses import JSONResponse
# from fastapi import Request
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     logger.error(f"Validation error: {exc}")
#     return JSONResponse(
#         status_code=422,
#         content={"detail": exc.errors(), "body": exc.body},
#     )


# @app.exception_handler(Exception)
# async def internal_server_error_handler(request: Request, exc: Exception):
#     logger.error(f"Internal Server Error: {str(exc)}", exc_info=True)  # Log the exception details
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal Server Error", "message": str(exc)},
#     )

# CORRECT_PASSCODE = "supersecretpasscode"

# total_cost_since_dict = {"date": datetime.now(),
#                          "input_cost": 0,
#                          "output_cost": 0}


# # Configure logging
# logger = logging.getLogger("Analyser")
# logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# # Initialize DI containers
# services = setup_dependencies()

# @app.on_event("startup")
# async def startup_event():
#     app.state.services = services
#     logger.info("Configurations loaded and services initialized")







