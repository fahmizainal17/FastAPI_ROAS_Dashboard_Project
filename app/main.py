from fastapi import FastAPI
from app.routers.Autoforecaster_module import router as autoforecaster_router
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_ROUTER_PREFIX = os.getenv("API_ROUTER_PREFIX")

app = FastAPI(
    title="FastAPI For ROAS Dashboard",
    summary="A collection of endpoints for FastAPI For ROAS Dashboard",
    version="0.1.0",
    docs_url=f"/{API_ROUTER_PREFIX}/docs",
    openapi_url=f"/{API_ROUTER_PREFIX}/openapi.json",
)


@app.get("/", response_class=HTMLResponse, summary="Welcome_Page", tags=["Root_Of_FastAPI_Application"])
def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to FastAPI For ROAS Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                text-align: center;
            }
            h1 {
                color: #333;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to FastAPI For ROAS Dashboard!</h1>
            <p>Thank you for visiting. This is the root of the application.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

app.include_router(autoforecaster_router, prefix=f"/{API_ROUTER_PREFIX}", tags=["Autoforecaster"])

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
