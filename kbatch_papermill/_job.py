"""
This is the kbatch-papermill job script

This file should be a standalone script with no local imports
"""

import os
import sys
from zipfile import ZipFile

import s3fs
from papermill.cli import papermill


def unzip_code():
    """
    Unzip the code directory from s3 prior to running papermill
    """
    s3_code_url: str | None = os.getenv("S3_CODE_URL")
    if s3_code_url is None:
        return

    print(f"Downloading {s3_code_url}")
    # rely on environment variables
    s3 = s3fs.S3FileSystem()

    with s3.open(s3_code_url) as f:
        zf = ZipFile(f)
        zf.extractall()

    # remove once consumed
    # TODO: remove after success to allow retries?
    # OOMKiller makes it hard to be sure any post-cleanup runs
    print(f"Deleting {s3_code_url}")
    s3.delete(s3_code_url)


def run_papermill():
    """Run a notebook with papermill"""
    # this is the papermill entrypoint
    # currently, papermill cli consumes arguments
    print(f"Running papermill with: {sys.argv}")
    papermill()


def main():
    unzip_code()
    run_papermill()
    # post-run?


if __name__ == "__main__":
    main()
