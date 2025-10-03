import logging
import time


logger = logging.getLogger(__name__)


class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Log request details before the view is called
        request_log_data = f"INCOMING REQUEST: {request.method} {request.path}"
        logger.info(request_log_data)

        response = self.get_response(request)

        # Log response details after the view is called
        duration = time.time() - start_time
        response_log_data = f"OUTGOING RESPONSE: {response.status_code} for {request.path} took {duration:.2f}s"
        logger.info(response_log_data)

        return response
