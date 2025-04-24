from collections.abc import Callable


def announce_start(name: str) -> Callable:
    def decorator(func: Callable):

        def wrapper(*args, **kwargs):
            print(f"Loading {name}...")
            temp = func(*args, **kwargs)
            print(f"Finished loading {name}!")
            return temp

        return wrapper

    return decorator
