from UserAuthModule.settings import tracer


def trace(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name(args[0])):
                result = func(*args, **kwargs)
                return result

        return wrapper

    return decorator
