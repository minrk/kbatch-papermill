"""
Submit papermill jobs
"""

import os
import shutil
import sys
from fnmatch import fnmatch
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import kbatch
import yaml
from kbatch import Job

_user = os.environ.get("JUPYTERHUB_USER", "user")


def _ignore_git(src, names):
    """ignore files likely to be unnededed and

    pangeo-fish with .git is too big to bundle.
    also exclude package metadata like build files and .egg-info
    """
    return [".git", "build"] + [name for name in names if fnmatch(name, "*.egg-info")]


def kbatch_papermill(
    notebook: Path,
    s3_dest: str,
    job_name: str = "papermill",
    *,
    s3_code_path: str = f"s3://gfts-ifremer/kbatch/{_user}",
    code_dir: str | None = None,
    profile_name: str = "default",
    env: dict[str, str] | None = None,
    parameters: dict[str, Any] | None = None,
) -> str:
    """Run a notebook with papermill and store the result in s3

    Args:
      notebook: path to notebook
      s3_dest: s3 URL where the notebook should be stored (e.g. s3://bucket/path/to/notebook.ipynb)
      job_name: name prefix for the kbatch job (default: papermill)
      profile_name: name of the profile to run with (specifies resource requirements)
      env: additional environment variables to set (AWS_ env will be set by default)
      parameters: papermill parameters to pass
    """

    notebook = Path(notebook)
    environment = dict()
    # unbuffer output
    environment["PYTHONUNBUFFERED"] = "1"
    # add AWS credentials for s3 output
    environment.update(
        {key: value for key, value in os.environ.items() if key.startswith("AWS_")}
    )
    if env:
        environment.update(env)

    if code_dir:
        code_dir = Path(code_dir)
        if notebook.is_file():
            relative_notebook = notebook.relative_to(code_dir)
        else:
            relative_notebook = notebook
        notebook_in_code = code_dir / relative_notebook
        if not notebook_in_code.exists():
            raise ValueError(f"{notebook_in_code} does not exist")
    else:
        relative_notebook = notebook.relative_to(notebook.parent)

    profile = kbatch._core.load_profile(profile_name)

    job = Job(
        name=job_name,
        image=os.environ["JUPYTER_IMAGE"],
        command=["mamba", "run", "--no-capture-output", "-p", sys.prefix],
        args=[
            "papermill",
            # progress bar doesn't work nicely in docker logs,
            # use log format instead
            "--log-output",
            "--no-progress-bar",
            # upload the notebook after each execution
            "--request-save-on-cell-execute",
            "-f",
            "_papermill_params.yaml",
            "--cwd",
            str(relative_notebook.parent),
            str(relative_notebook),
            s3_dest,
        ],
        env=environment,
    )
    with TemporaryDirectory() as td:
        td_path = Path(td)
        if code_dir:
            shutil.copytree(code_dir, td_path, ignore=_ignore_git, dirs_exist_ok=True)
        else:
            shutil.copyfile(notebook, td_path / notebook.name)
        with (td_path / "_papermill_params.yaml").open("w") as f:
            yaml.dump(parameters or {}, f)

        kubernetes_job = kbatch.submit_job(job, profile=profile, code=td_path)
    return kubernetes_job["metadata"]["name"]
