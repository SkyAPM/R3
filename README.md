# R3 

<img src="r3.png" alt="r3 logo" height="150px" align="right" />

**R3**: <ins>R</ins>ESTful Patte<ins>r</ins>n <ins>R</ins>ecognition (R3) for the Apache SkyWalking AI pipeline.



### What is R3?
Modern APIs are often written in a RESTful convention. For example, the below endpoint contains four parameters, meaning each instance of this endpoint will be different although they share the same pattern.

`/api/v{apiVersion}/artists/{artistid}/moments/{postid}/comments/{commentid}`

While the DevOps team could setup rules for grouping such URI patterns, it quickly gets overwhelming when there are numerous endpoints across services. 

R3 is a project that entirely eliminates the need for writing complex expressions to group RESTful endpoints for runtime performance analysis tasks.

**IMPORTANT** The R3 algorithm is based on machine learning and, as with any algorithm, it doesn't guarantee 100% accuracy (still, it's highly accurate). 
However, it offers a powerful and convenient solution for grouping RESTful endpoints in any scenario.

### Getting Started
Currently, R3 offers a simple gRPC service that could be deployed easily at local or containerized environments.

#### Simple Server (Multiprocessing Producer Consumer)

The simple server is the best way to get started, which could steadily serve 500+ SkyWalking services * 3000 uris per minute). 

To run the R3 service on localhost:

```bash
python -m servers.simple.run
```

To deploy as a container:

```bash
docker run -d --name r3 -p 17128:17128 r3:latest 
```

#### Environment Variables

R3 supports configuration through environment variables. Key variables include:

- **`LOG_LEVEL`**: Controls logging verbosity (default: `INFO`)
  - Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - **Production recommendation**: Set to `ERROR` to minimize log volume and prevent disk space issues in Docker containers
  - Example: `docker run -d --name r3 -e LOG_LEVEL=ERROR -p 17128:17128 r3:latest`

- **`DRAIN_SIM_TH`**: Similarity threshold for clustering (default: `0.4`)
- **`DRAIN_ANALYSIS_MIN_URL_COUNT`**: Minimum URLs to trigger analysis (default: `20`)
- **`SNAPSHOT_FILE_PATH`**: Directory for snapshot persistence (default: `/tmp/`)

For a complete list of configuration options, see [Configuration](models/Configuration.md).

### Demo

#### Restful Pattern Recognition

The following URL would recognize the pattern as `/api/users/{var}`, since the last part of URL are different for each instance.

* /api/users/cbf11b02ea464447b507e8852c32190a
* /api/users/5e363a4a18b7464b8cbff1a7ee4c91ca
* /api/users/44cf77fc351f4c6c9c4f1448f2f12800
* /api/users/38d3be5f9bd44f7f98906ea049694511
* /api/users/5ad14302e7924f4aa1d60e58d65b3dd2

#### Word Detection

The following URL would keep the original URL, not parametrized, since the all part of URL are word.

* /api/sale
* /api/product_sale
* /api/ProductSale

If the words are customized, not a word. Such as some application name, such as `hikaricp`, then R3 support customized word. 
Please refer to the [configuration](models/Configuration.md) `customized_words_file` for more details.

#### Lower Sample Count

The following URL would keep the original URL, not parametrized, since the sample count is lower than the threshold(`combine_min_url_count`).
If the sample count equals or bigger than the threshold, the URL would be parametrized.

Such as the threshold is `3`, the following URL would keep the original URL, not parametrized.

* /api/fetch1
* /api/fetch2

But the following URL would be parametrized to `/api/{var}`, since the sample count is bigger than the threshold.

* /api/fetch1
* /api/fetch2
* /api/fetch3

#### Versioned API

If the part of URI contains version number, such as `v1`, `v2`, `v3`, the version number part would not be parametrized.

Such as the following URL would not be parametrized:

* /test/v1
* /test/v2
* /test/v3

If still not matter the other part of URI to be parametrized, such as the following URI would be parametrized to `/test/v1/{var}` and `/test/v999/{var}`.

* /test/v1/cbf11b02ea464447b507e8852c32190a
* /test/v1/5e363a4a18b7464b8cbff1a7ee4c91ca
* /test/v1/38d3be5f9bd44f7f98906ea049694511
* /test/v999/1
* /test/v999/2
* /test/v999/3

### Algorithm: URIDrain
If you are curious how the algorithm actually works or decided to improve upon it, please first read the [URIDrain Overview](models/README.md) and checkout the algorithm live demo by running below commands:

To run a demo of the algorithm (implemented with [Gradio](https://gradio.app/)):

1. Install the dependencies with `make install` (or `make env` if you plan to contribute code)
2. Run `python demo.demo_gradio`
3. Open `http://localhost:8080` in your browser or access through remote gradio service from the web by setting `launch(share=True)`
4. Enjoy!


### Licenses
This project is dual-licensed under MIT and Apache 2.0.

The URIDrain algorithm implemented in this project is a modified version of the upstream [Drain3](https://github.com/logpai/Drain3) log clustering algorithm. 

Therefore, the modified algorithm is also licensed under MIT as the upstream. The remaining utilities and services are licensed under Apache 2.0, which also allows commercial usage as long as users adhere to the license terms.

### Contributing
We welcome contributions from the community to make R3 more robust. Whether it's bug fixes, feature enhancements, or new ideas, your input is valuable.