# Python IDE for OpenRouter - Version 1.0
# Automotive Chat Assistant with Code Execution
import os
from app import app

if __name__ == "__main__":
    # Disable debug mode for production
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
