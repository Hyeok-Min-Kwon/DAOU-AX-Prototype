from fastapi import FastAPI

app = FastAPI(
    title="BizPpurio AI Optimizer",
    description="AI-driven optimization for enterprise message campaigns",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
