import json

from pathlib import Path

from models import SandboxConfig


def load_json_template(file_path: str | Path) -> SandboxConfig | None:
    """
    load json template file.

    Args:
        file_path: the path of the config file.

    Return:
        SandboxConfig: the loaded model.
        None: if any errors occurs.
    """
    file = Path(file_path)

    try:
        with open(file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            config = SandboxConfig.model_validate(raw)
            return config

    except FileNotFoundError:
        print(f"FileNotFoundError : '{file}' does not exists !")
    except PermissionError:
        print(f"PermissionError : you do not have the rights to open '{file}'.")
    except IsADirectoryError:
        print(f"IsADirectoryError : '{file}' is a directory!")
    except json.JSONDecodeError as e:
        print(f"JSONError : Invalid json file, parsing at (line {e.lineno}, column {e.colno}).")
    except Exception as e:
        print(f"Error: {e}")

    return None


def load_python_file(file_path: str | Path) -> str | None:
    """
    load python file's content.

    Args:
        file_path: the path of the python file.

    Return:
        str: the python code.
        None: if any errors occurs.
    """

    file = Path(file_path)

    if not file.suffix == ".py":
        print("Error: The file must be a python file.")
        return None

    if not file.is_file():
        print(f"Error: Unable to load {file_path}")
        return None

    try:
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()
            return code

    except FileNotFoundError:
        print(f"FileNotFoundError : '{file}' does not exists !")
    except PermissionError:
        print(f"PermissionError : you do not have the rights to open '{file}'.")
    except IsADirectoryError:
        print(f"IsADirectoryError : '{file}' is a directory!")
    except Exception as e:
        print(f"Error: {e}")

    return None
