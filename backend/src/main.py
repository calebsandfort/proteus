from dotenv import load_dotenv

load_dotenv()

from ag_ui_langgraph import add_langgraph_fastapi_endpoint  # noqa: E402
from ag_ui_langgraph import LangGraphAgent  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from src.agent.graph import agent  # noqa: E402
from src.api.health import router as health_router  # noqa: E402
from src.api.router import api_router  # noqa: E402
from src.config import settings  # noqa: E402

app = FastAPI(title="Proteus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint at /health (no prefix)
app.include_router(health_router)

# CopilotKit and other API endpoints at /api/*
app.include_router(api_router, prefix="/api")

copilot_agent = LangGraphAgent(
    name="chat_agent",
    description="A helpful AI chat assistant.",
    graph=agent,
)

add_langgraph_fastapi_endpoint(app, copilot_agent, "/copilotkit")
