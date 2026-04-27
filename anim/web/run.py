"""Run SynapseFlow dashboard."""

import os

from dotenv import load_dotenv
load_dotenv()
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "anim.web.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
