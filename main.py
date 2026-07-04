import logging
import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logging.basicConfig(level=logging.INFO)

    uvicorn.run(
        "zai.api:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
