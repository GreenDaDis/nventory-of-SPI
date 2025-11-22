# app.py
from aiohttp import web
import logging
from handlers.agent import agent_data_handler
import json


class ServerApp:
    """
    Main server application using aiohttp
    """

    def __init__(self, host: str = '0.0.0.0', port: int = 8000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.received_data = []
        self.setup_logging()
        self.setup_routes()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ServerApp")

    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post('/api/v1/agent/data', agent_data_handler)

        # Basic health check
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/', self.root_handler)

    async def health_handler(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "received_reports": len(self.received_data)
        })

    async def root_handler(self, request):
        """Root endpoint"""
        return web.json_response({
            "message": "System Inventory Server is running",
            "endpoint": "POST /api/v1/agent/data"
        })

    def run(self):
        """Run the server"""
        self.logger.info(f"Starting server on {self.host}:{self.port}")
        print(f"🚀 System Inventory Server starting...")
        print(f"📍 URL: http://{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}")
        print(
            f"📨 Agent data endpoint: POST http://{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}/api/v1/agent/data")
        print("Press Ctrl+C to stop the server\n")

        web.run_app(
            self.app,
            host=self.host,
            port=self.port,
            print=None  # Disable aiohttp default logging
        )


# Create global app instance
app_instance = ServerApp()

# Export app for uvicorn/gunicorn if needed
app = app_instance.app

if __name__ == "__main__":
    app_instance.run()