"""
kbatch interface

wraps kbatch for some nicer Python APIs

Maybe some of this should be in kbatch
"""

import time

import kbatch
import rich
from IPython.display import clear_output, display
from ipywidgets import Output
from tqdm.notebook import tqdm


def print_job_status():
    """Print the status of all kbatch jobs as a nice table."""
    rich.print(kbatch._core.format_jobs(kbatch.list_jobs()))


def wait_for_jobs(*job_names, stop_on_failure=True, failure_logs=True):
    """Wait for one or more jobs by name.

    :param job_names: Job names, default to all names.
    :type job_names: list[str]
    :param stop_on_failure: Whether to stop waiting on the first failure, default to True.
    :type stop_on_failure: bool
    :param failure_logs: Whether to print the logs of failed logs, default to True.
    :type failure_logs: bool
    """
    if not job_names:
        job_names = [job["metadata"]["name"] for job in kbatch.list_jobs()["items"]]
    all_job_names = set(job_names)
    watch_job_names = set(all_job_names)
    failed = []
    progress = tqdm(total=len(all_job_names), desc="jobs")
    out = Output()
    display(out)
    with out:
        print_job_status()

    while watch_job_names:
        jobs = kbatch.list_jobs()["items"]
        job_names = set(job["metadata"]["name"] for job in jobs)
        removed_jobs = watch_job_names.difference(job_names)
        if removed_jobs:
            progress.update(len(removed_jobs))
            print(f"No such jobs: {', '.join(removed_jobs)}")
            watch_job_names -= removed_jobs
        jobs = [job for job in jobs if job["metadata"]["name"] in watch_job_names]
        for job in jobs:
            name = job["metadata"]["name"]
            if not job["status"]["active"]:
                progress.update(1)
                watch_job_names.remove(name)
                if job["status"]["failed"]:
                    failed.append(name)
                    if stop_on_failure:
                        break
        if watch_job_names:
            progress.refresh()
            time.sleep(1)
            with out:
                clear_output(wait=True)
                print_job_status()
    progress.close()
    for job_name in failed:
        if failure_logs:
            print(kbatch.job_logs(job_name))
        else:
            print(f"{job_name} failed")
