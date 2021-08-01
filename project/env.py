"""Get env file in package. python-dotenv doesn't seem to work with python2"""
import os
import re
import json


def get_env():
    """Get the env in path."""
    def _parse_env(env):
        """Parse env for variable placeholders and substitute if necessary."""

        for key in env:
            sub = re.sub(r'\$' + key, env[key], json.dumps(env))

        return json.loads(sub)

    def _convert_env(env_file):
        """Parse and convert the env file to a dictionary type."""
        env = {}

        for key in re.finditer(r'(.+?)="(.+)"', env_file,  re.M):
            env[key.group(1)] = key.group(2)

        return _parse_env(env)

    if os.path.exists('.env'):
        with open('.env') as file:
            env = _convert_env(file.read())
            return env

    raise FileNotFoundError
