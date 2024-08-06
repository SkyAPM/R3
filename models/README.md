### Algorithm: URIDrain

URIDrain is a robust online URI sequence clustering algorithm based on the [Drain3](https://github.com/logpai/Drain3)
algorithm.

The original paper of Drain can be found [here](https://jiemingzhu.github.io/pub/pjhe_icws2017.pdf)
and [here](https://arxiv.org/pdf/1806.04356.pdf).

The configuration please refer to [Configuration Documentation](./Configuration.md).

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

**Known Caveats**:
The algorithm may provide false clustering in some edge cases (although it doesn't hurt at all in APM scenarios). 
The caveat is led by the fact that some different endpoints may contain common params accidentally
in extremely rare cases (When the incoming sequence order is in bad luck). Example:
```text
cur_sim = 0.25 for cluster 1, cluster.log_template_tokens = ('api', 'v2', 'customers', 'xyz789') with param count = 0
cur_sim = 0.5 for cluster 3, cluster.log_template_tokens = ('api', 'v1', 'projects', '<:VAR:>') with param count = 1
cur_sim = 0.75 for cluster 7, cluster.log_template_tokens = ('api', 'v1', 'wallets', 'abcdef') with param count = 0
cur_sim = 0.5 for cluster 8, cluster.log_template_tokens = ('api', 'v1', 'bills', 'abcxyz') with param count = 0
cur_sim = 0.5 for cluster 9, cluster.log_template_tokens = ('api', 'v1', 'services', 'abc456') with param count = 0
cur_sim = 0.75 for cluster 12, cluster.log_template_tokens = ('api', 'v1', 'companies', 'xyz123') with param count = 0
seq1 (incoming uri) = api/v1/companies/abcdef
seq2 (matched template) = api/v1/wallets/abcdef
```
another example
```text
seq1 (matched 1) = api/v1/haha/456/anotherpath2

seq1 (incoming uri) = api/v1/haha/456/actualpath1

seq2 (matched 2) = api/v1/haha/123/actualpath1
```
This can be mitigated with NLTK to detect which tokens are likely to be parameters. This is not implemented yet.

General rule is: do not trust a template that only have size 1 and has no params identified: it's likely to be a false classification.

TODO: Add postprocessing for such single templates (it's single because algorithm has preference for correct template with param count. 
(IFF template is size 1 and has no params and is almost identical to another template, merge them)

### Integration
This project rely on gRPC to communicate with the Apache SkyWalking AI pipeline. The gRPC service definition can be found
in the `server/proto/' folder. 

Compile the proto by running `make gen` or simply `make env` if you are get started from a bare environment.

### TODO
Try catch statements to handle uncovered algorithm errors

