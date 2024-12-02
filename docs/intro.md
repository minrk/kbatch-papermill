# Introduction

Designed for [Destination-Earth GFTS](https://github.com/destination-earth/DestinE_ESA_GFTS), `kbatch_papermill` runs notebooks with [papermill] on Kubernetes via [kbatch].

**DISCLAIMER:** the package does not currently target general use because the following assumptions, specific to GFTS deployments, are made:

1. Default AWS credentials are set up via environment variables, and work.
2. Jobs should always run with the same $JUPYTER_IMAGE as the submitting environment.
3. $JUPYTER_IMAGE has `papermill`.
4. We have read/write access to S3 for _both_ the code input directory and the output directory (completed job results).


We also add some generic functionality to make a nicer Python API for kbatch, which should perhaps be upstreamed. See `_kbatch.py` for most of that.

Besides, we overcome the size limit of the commonly used [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) approach by passing the code directory (currently to S3) instead.

[papermill]: https://papermill.readthedocs.io
[kbatch]: https://kbatch.readthedocs.io
