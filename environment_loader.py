import json
from pathlib import Path
from typing import Callable, Any, Optional


class EnvironmentWrapper:
    """
    A context manager that wraps a single environment variable value.

    Used to temporarily access an environment value within a `with` block.
    """

    def __init__(self, key: str, value):
        self.key = key
        self.value = value

    def __enter__(self, *args, **kwargs):
        return self.value

    def __exit__(self): ...


class Environment:
    """
    Loads and provides access to a JSON-based environment configuration.

    Supports retrieval of environment variables with optional transformation,
    nested environments, and context-managed access.
    """

    def __init__(self, path: Optional[str]):
        """
        Initialize the environment from a JSON file at the given path.

        If path is None, initializes an empty environment.
        """

        if path is not None:
            with open(Path(path), encoding="utf-8") as file:
                self.env = json.load(file)
        else:
            self.env = None

    def __call__(
        self, name: str, default=None, transform: Callable[[Any], Any] = lambda x: x
    ):
        """
        Enables callable access to environment values, returning a context manager.

        Parameters:
            name: The key to look up.
            default: The value to return if the key is not found.
            transform: A function to transform the value before returning.

        Returns:
            An EnvironmentWrapper for use in a `with` statement.
        """

        return EnvironmentWrapper(name, transform(self.env.get(name, default)))

    def take(self, name: str):
        """
        Extract a nested environment dictionary and return it as a new Environment.

        Parameters:
            name: The key pointing to a nested dictionary.

        Returns:
            A new Environment instance wrapping the nested dictionary, or None.
        """

        desired_env = self.get(name)
        if desired_env is None:
            return None

        new_env = Environment(None)
        new_env.env = desired_env
        return new_env

    def get(
        self, name: str, default=None, transform: Callable[[Any], Any] = lambda x: x
    ):
        """
        Retrieve a value from the environment with optional transformation.

        Parameters:
            name: The key to retrieve.
            default: Value to return if the key is missing.
            transform: A function to apply to the value before returning.

        Returns:
            The retrieved and transformed value.
        """
        return transform(self.env.get(name, default))

    def __getitem__(self, item):
        return self.env[item]
