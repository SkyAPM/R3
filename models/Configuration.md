## Configuration

All configurations in URI Drain are done using `uri_drain.ini` file. [Here is a specific demo](../servers/simple/uri_drain.ini).

### Snapshot

Snapshot is used to serialize and store the analysis results that have been saved in the current system. 
Currently, it supports saving snapshots to the file system.

| Name                      | Type(Unit)  | Default | Description                                                                               |
|---------------------------|-------------|---------|-------------------------------------------------------------------------------------------|
| file_dir                  | string      | /tmp/   | The directory to save the snapshot, the persistent would disable when the value is empty. |
| snapshot_interval_minutes | int(minute) | 10      | The interval to save the snapshot.                                                        |
| compress_state            | bool        | True    | Whether to compress the snapshot through zlib with base64.                                |

### Masking

When aggregation methods are detected, Masking determines how to generate the aggregation information.

Currently, all similar content is replaced with `{var}` by default.

| Name        | Type(Unit) | Default | Description                       |
|-------------|------------|---------|-----------------------------------|
| mask_prefix | string     | {       | The prefix to mask the parameter. |
| mask_suffix | string     | }       | The suffix to mask the parameter. |

### Drain

Drain is the core algorithm of URI Drain. 

| Name             | Type(Unit) | Default | Description                                                                                                                                                          |
|------------------|------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| sim_th           | float      | 0.4     | The similarity threshold to decide if a new sequence should be merged into an existing cluster.                                                                      |
| depth            | int        | 4       | Max depth levels of pattern. Minimum is 2.                                                                                                                           |
| max_children     | int        | 100     | Max number of children of an internal node.                                                                                                                          |
| max_clusters     | int        | 1024    | Max number of tracked clusters (unlimited by default). When this number is reached, model starts replacing old clusters with a new ones according to the LRU policy. |
| extra_delimiters | string     | /       | The extra delimiters to split the sequence.                                                                                                                          |

### Profiling

Profiling is used to enable the profiling of the algorithm.

| Name       | Type(Unit)  | Default | Description                                       |
|------------|-------------|---------|---------------------------------------------------|
| enabled    | bool        | False   | Whether to enable the profiling.                  |
| report_sec | int(second) | 30      | The interval to report the profiling information. |