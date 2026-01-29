"""Real-time events (SSE) API routes"""

from flask import Response
import json
import time
from queue import Queue, Empty

def create_event_routes(app, api_server):
    """Create SSE event routes"""
    
    @app.route('/api/v1/events/stream', methods=['GET'])
    def event_stream():
        """SSE endpoint for real-time events"""
        
        def generate():
            # Create subscriber queue
            subscriber_id = str(time.time())
            queue = Queue(maxsize=50)
            
            with api_server._sse_lock:
                api_server._sse_subscribers[subscriber_id] = queue
            
            try:
                # Send connection message
                yield f"data: {json.dumps({'type': 'connected', 'subscriber_id': subscriber_id})}\n\n"
                
                # Stream events
                while True:
                    try:
                        event = queue.get(timeout=30)
                        yield f"data: {json.dumps(event)}\n\n"
                    except Empty:
                        # Keep-alive
                        yield f": keep-alive\n\n"
            
            finally:
                # Cleanup
                with api_server._sse_lock:
                    if subscriber_id in api_server._sse_subscribers:
                        del api_server._sse_subscribers[subscriber_id]
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )