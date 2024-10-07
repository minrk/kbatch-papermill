"""
Submit papermill jobs
"""

import os
import shutil
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from secrets import token_urlsafe
from shutil import make_archive
from tempfile import TemporaryDirectory
from typing import Any

import kbatch
import s3fs
import yaml
from kbatch import Job

_user = os.environ.get("JUPYTERHUB_USER", "user")
_job_py = Path(__file__).parent.resolve() / "_job.py"


def _ignore_git(src, names):
    """ignore files likely to be unnededed and

    pangeo-fish with .git is too big to bundle.
    also exclude package metadata like build files and .egg-info
    """
    return [".git", "build"] + [name for name in names if fnmatch(name, "*.egg-info")]


def _upload_code_dir(
    s3_base: str,
    notebook,
    parameters: dict[str, Any],
    code_dir: Path | None = None,
    s3: s3fs.S3FileSystem | None = None,
) -> str:
    """
    Upload code directory to s3, return the URL
    """
    if s3 is None:
        s3 = s3fs.S3FileSystem(anon=False)
    s3_base = s3_base.rstrip("/")
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    date_slug = now.strftime("%H%M%S")
    random_slug = token_urlsafe(3)
    code_name = f"{notebook.stem}-{date_slug}-{random_slug}"

    code_url = f"{s3_base}/{date_path}/{code_name}.zip"
    if s3.exists(code_url):
        raise ValueError(f"{code_url} already exists!")
    with TemporaryDirectory() as td:
        td_path = Path(td)
        temp_code = td_path / "code"
        if code_dir:
            shutil.copytree(code_dir, temp_code, ignore=_ignore_git, dirs_exist_ok=True)
        else:
            temp_code.mkdir()
            shutil.copyfile(notebook, temp_code / notebook.name)
        # add papermill params
        with (temp_code / "_papermill_params.yaml").open("w") as f:
            yaml.dump(parameters or {}, f)
        zip_path = make_archive(td_path / "_code", "zip", temp_code)
        s3.put_file(zip_path, code_url)
    return code_url


def kbatch_papermill(
    notebook: Path,
    s3_dest: str,
    job_name: str = "papermill",
    *,
    s3_code_dir: str,
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

    s3_code_url = _upload_code_dir(
        s3_code_dir, notebook, parameters=parameters, code_dir=code_dir
    )
    environment["S3_CODE_URL"] = s3_code_url

    job = Job(
        name=job_name,
        image=os.environ["JUPYTER_IMAGE"],
        command=["mamba", "run", "--no-capture-output", "-p", sys.prefix],
        args=[
            "python3",
            _job_py.name,
            # progress bar doesn't work nicely in docker logs,
            # use log format instead
            "--log-output",
            "--no-progress-bar",
            # upload the notebook after each execution
            "--request-save-on-cell-execute",
            # save every minute for long-running cells
            "--autosave-cell-every=60",
            "-f",
            "_papermill_params.yaml",
            "--cwd",
            str(relative_notebook.parent),
            str(relative_notebook),
            s3_dest,
        ],
        env=environment,
    )
    try:
        kubernetes_job = kbatch.submit_job(job, profile=profile, code=_job_py)
    except Exception:
        # cleanup s3 if it fails
        s3 = s3fs.S3FileSystem(anon=False)
        s3.remove(s3_code_url)
        raise
    return kubernetes_job["metadata"]["name"]
