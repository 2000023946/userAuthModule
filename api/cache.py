import threading


class QueryCacheSingleton:
    _thread_local = threading.local()

    @classmethod
    def get_cache(cls):
        """Return the thread-local cache dictionary, creating it if missing."""
        if not hasattr(cls._thread_local, "cache"):
            cls._thread_local.cache = {}  # New cache for this thread/request
        return cls._thread_local.cache

    @classmethod
    def get_or_set(cls, key, func):
        """Return cached value if exists, otherwise compute and store it."""
        cache = cls.get_cache()
        if key not in cache:
            cache[key] = func()  # Execute DB query only once per request
        return cache[key]

    @classmethod
    def clear(cls):
        """Clear the thread-local cache at the end of the request."""
        cls._thread_local.cache = {}


# import threading
# import time

# MAX_THREADS = 2
# semaphore = threading.Semaphore(MAX_THREADS)

# # Simulate a database query
# def fake_db_query(key):
#     print(f"Executing DB query for {key}")
#     time.sleep(1)  # simulate query delay
#     return f"Result for {key}"

# # Simulate a request handler
# def handle_request(request_id):
#     # Check if semaphore is available
#     if semaphore._value == 0:  # internal counter, just for demo
#         print(f"Request {request_id} is waiting for a free thread...")

#     with semaphore:  # Only MAX_THREADS requests can run concurrently
#         print(f"Request {request_id} started")

#         result1 = QueryCacheSingleton.get_or_set(f"user:{request_id}", lambda: fake_db_query(request_id))
#         print(f"Request {request_id} first fetch: {result1}")

#         result2 = QueryCacheSingleton.get_or_set(f"user:{request_id}", lambda: fake_db_query(request_id))
#         print(f"Request {request_id} second fetch: {result2}")

#         QueryCacheSingleton.clear()
#         print(f"Request {request_id} cache cleared\n")
#         time.sleep(0.5)  # simulate extra work

# # Simulate 3 requests with only 2 threads allowed at a time
# threads = []
# for i in range(3):
#     t = threading.Thread(target=handle_request, args=(i,))
#     threads.append(t)
#     t.start()

# for t in threads:
#     t.join()
