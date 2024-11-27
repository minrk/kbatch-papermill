# kbatch-papermill

Currently designed for [Destination-Earth GFTS](https://github.com/destination-earth/DestinE_ESA_GFTS), it runs notebooks with [papermill] on Kubernetes via [kbatch].
It does not currently target general use because the following assumptions, specific to GFTS deployments, are made:

1. Default AWS credentials are set up via environment variables, and work.
2. Jobs should always run with the same $JUPYTER_IMAGE as the submitting environment.
3. $JUPYTER_IMAGE has `papermill`.
4. We have read/write access to S3 for _both_ the code input directory and the output directory (completed job results).

Note that we do not use the [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) approach to pass the code directory, because of the size limit on config maps.
So we essentially replicate the code directory functionality of kbatch, but store in S3 instead.

We also add some generic functionality to make a nicer Python API for kbatch, which should perhaps be upstreamed. See `_kbatch.py` for most of that.

[papermill]: https://papermill.readthedocs.io
[kbatch]: https://kbatch.readthedocs.io
