# kbatch-papermill

run notebooks with [papermill] on kubernetes via [kbatch], currently designed for [Destination-Earth GFTS](https://github.com/destination-earth/DestinE_ESA_GFTS).

Not currently targeting general use because we're making the following assumptions specific to the GFTS deployment:

1. default AWS credentials are set up via environment variables, and work
2. jobs should always run with the same $JUPYTER_IMAGE as the submitting environment
3. $JUPYTER_IMAGE has papermill
4. we have read/write access to s3 for both the code input directory and the completed job results

The ConfigMap approach to passing the code directory doesn't work great for us due to the size limit on config maps.
So we essentially replicate the code directory functionality of kbatch,
but store in s3 instead.

Some generic functionality is here to make a nicer Python API for kbatch,
which should perhaps be upstreamed. See `_kbatch.py` for most of that.

[papermill]: https://papermill.readthedocs.io
[kbatch]: https://kbatch.readthedocs.io
