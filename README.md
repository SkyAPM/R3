# R3

RESTful Pattern Recognition(R3) for Apache SkyWalking AI pipeline.

### Demo

To run a demo of the algorithm (integration is pending to SkyWalking):

1. Install the dependencies with `make env`
2. CD into this folder and run `python demo/demo_gradio.py`
3. Open `http://localhost:8080` in your browser or access through remote gradio url from the web by setting `launch(share=True)`
4. Enjoy!

### Algorithm: URIDrain

URIDrain is a robust online URI sequence clustering algorithm based on the [Drain3](https://github.com/logpai/Drain3)
algorithm.

The original paper of Drain can be found [here](https://jiemingzhu.github.io/pub/pjhe_icws2017.pdf)
and [here](https://arxiv.org/pdf/1806.04356.pdf).

#### Upstream Drain3 version

- Currently
  at [e0e942886845315ec4eac8b8de68859d9e106908](https://github.com/logpai/Drain3/commit/e0e942886845315ec4eac8b8de68859d9e106908)

#### How URIDrain works?

URIDrain operates by maintaining a fixed-depth tree on the URI sequences. Each node in the tree represents a unique
characteristic token. The tree is traversed to find the best matching cluster for a new URI sequence, it's an
incremental algorithm. If no matching cluster is found, a new cluster is created, otherwise, the matching cluster will
be updated if needed to reflect the new URI sequence.

In addition to the Drain3 algorithm, the URIDrain adds several key improvements to adapt the log clustering problem to
the URI domain. Which includes:

1. The URIDrain algorithm is designed to work with diverse URI sequences of different lengths and formats.
2. The matching threshold is **dynamically** calculated given the characteristics of the URI sequences.
3. The URIDrain algorithm doesn't involve pre-masking of the URI sequences to prevent false assumptions.
4. The URIDrain algorithm takes preceding and subsequent URI tokens into account when deciding if a matched cluster
   should be updated.
5. **TODO**: The URIDrain algorithm optionally use English Corpus to help identify likely non-parameter tokens.