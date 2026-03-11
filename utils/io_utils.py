"""I/O utility functions for reading and writing common neuroimaging data formats."""

import glob
import json
import os

import pandas as pd


def load_tsv(tsv_path, **kwargs):
    """Load a TSV file as a pandas DataFrame.

    Args:
        tsv_path (str): Path to the TSV file.
        **kwargs: Additional keyword arguments passed to pandas.read_csv.

    Returns:
        pandas.DataFrame: Loaded data.

    Raises:
        FileNotFoundError: If the TSV file does not exist.
        ValueError: If the file cannot be parsed as TSV.
    """
    if not os.path.isfile(tsv_path):
        raise FileNotFoundError(f"TSV file not found: {tsv_path}")
    try:
        return pd.read_csv(tsv_path, sep="\t", **kwargs)
    except Exception as exc:
        raise ValueError(f"Could not parse TSV file '{tsv_path}': {exc}") from exc


def save_tsv(df, tsv_path):
    """Save a pandas DataFrame as a TSV file.

    Args:
        df (pandas.DataFrame): DataFrame to save.
        tsv_path (str): Destination path for the TSV file.

    Returns:
        str: Absolute path to the saved file.

    Raises:
        TypeError: If df is not a pandas DataFrame.
        OSError: If the file cannot be written.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df).__name__}.")
    ensure_dir(os.path.dirname(os.path.abspath(tsv_path)))
    try:
        df.to_csv(tsv_path, sep="\t", index=False)
    except OSError as exc:
        raise OSError(f"Could not write TSV file '{tsv_path}': {exc}") from exc
    return os.path.abspath(tsv_path)


def load_json(json_path):
    """Load a JSON file and return its contents as a Python object.

    Args:
        json_path (str): Path to the JSON file.

    Returns:
        dict or list: Parsed JSON contents.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the file is not valid JSON.
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse JSON file '{json_path}': {exc}") from exc


def save_json(data, json_path, indent=2):
    """Save a Python object as a JSON file.

    Args:
        data (dict or list): Data to serialise.
        json_path (str): Destination path for the JSON file.
        indent (int, optional): Number of spaces used for indentation. Defaults to 2.

    Returns:
        str: Absolute path to the saved file.

    Raises:
        TypeError: If data is not JSON-serialisable.
        OSError: If the file cannot be written.
    """
    ensure_dir(os.path.dirname(os.path.abspath(json_path)))
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent)
    except TypeError as exc:
        raise TypeError(f"Data is not JSON-serialisable: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not write JSON file '{json_path}': {exc}") from exc
    return os.path.abspath(json_path)


def ensure_dir(path):
    """Create a directory (and any intermediate parents) if it does not exist.

    Args:
        path (str): Directory path to create.

    Returns:
        str: Absolute path to the directory.

    Raises:
        OSError: If the directory cannot be created.
    """
    if not path:
        return path
    abs_path = os.path.abspath(path)
    try:
        os.makedirs(abs_path, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Could not create directory '{abs_path}': {exc}") from exc
    return abs_path


def find_files(root_dir, pattern):
    """Find files matching a glob pattern recursively under root_dir.

    Args:
        root_dir (str): Root directory to search from.
        pattern (str): Glob pattern (e.g. ``'**/*.nii.gz'``).

    Returns:
        list[str]: Sorted list of absolute paths matching the pattern.

    Raises:
        FileNotFoundError: If root_dir does not exist.
    """
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Directory not found: {root_dir}")
    search_pattern = os.path.join(os.path.abspath(root_dir), pattern)
    matches = glob.glob(search_pattern, recursive=True)
    return sorted(os.path.abspath(p) for p in matches)
