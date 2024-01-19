#  Copyright 2024 SkyAPM org
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""
Run this file to get a web demo of the URI Drain algorithm.
"""
import io
import os
import sys
import time
from collections import defaultdict
from os.path import dirname

import gradio
import gradio as gr
import pandas as pd
from models.uri_drain.template_miner import TemplateMiner
from models.uri_drain.template_miner_config import TemplateMinerConfig

clusters = ''
cluster_templates = []
uri_to_cluster = defaultdict(list)

back_to_top_btn_html = '''<button id="toTopBtn" onclick="window.scrollTo({ top: 0, behavior:'smooth'});" 
style="border: 2px solid black; position: fixed; bottom: 60px; right: 20px;"> <a style="color:black; 
text-decoration:none; font-size: 20px;">Back to Top!</a> </button>

'''


def cluster_uris(table: str, shuffle, seed):  # already loaded into a string
    if table == '':
        raise gradio.Error('😵 Please upload a valid txt file or choose a sample! 😵')
    dataset = pd.DataFrame([uri for uri in table.split('\n')])
    if shuffle:  # Shuffle dataset based on random.seed
        if not seed.isdigit():
            raise gradio.Error('😵 Please enter a valid seed (Integer) ! 😵')
        dataset = dataset.sample(frac=1, random_state=int(seed))
    global clusters
    global cluster_templates
    global uri_to_cluster
    uri_to_cluster = defaultdict(list)
    cluster_templates = []
    clusters = ''
    config = TemplateMinerConfig()
    config.load(dirname(__file__) + "/uri_drain.ini")
    template_miner = TemplateMiner(config=config)
    # Add logs to the template miner
    timer_start = time.time()
    dataset_size = len(dataset)
    print(f'RUN: shuffle is {shuffle}, seed is {seed} for dataset size {dataset_size}')

    for line_no, uri in dataset.itertuples():
        if uri == '':
            continue
        # print(f'working on uri {uri}')
        result = template_miner.add_log_message(uri)
        # print(f'result is {result}')
        uri_to_cluster[str(result['cluster_id'])].append(uri)
    time_taken = time.time() - timer_start
    print(f'Total time spent to process {dataset_size} endpoints is {time_taken:.3f} seconds')
    captured_output = io.StringIO()
    sys.stdout = captured_output
    template_miner.drain.print_tree(max_clusters=1000)
    # Get the captured output as a string
    printed_tree_max1000 = captured_output.getvalue()

    # Restore the original stdout
    sys.stdout = sys.__stdout__
    clusters = printed_tree_max1000
    # Get clusters
    clusters = template_miner.drain.clusters

    sorted_clusters = sorted(template_miner.drain.clusters, key=lambda it: (it.size, len(it.get_template())),
                             reverse=True)

    cluster_templates = [f'{cluster.cluster_id}::{cluster.get_template()} (Size={cluster.size})' for cluster in
                         sorted_clusters]

    def get_regex(cluster):
        return template_miner._get_template_parameter_extraction_regex(cluster.get_template(), exact_matching=True)

    sorted_clusters_without_regex = '\n'.join(f'Cluster:: {str(cluster)}'
                                              for cluster in sorted_clusters)
    sorted_clusters_with_regex: str = '====\n\n'.join(f'Cluster:: {str(cluster)}\nREGEX:: {get_regex(cluster)}'
                                                for cluster in sorted_clusters)
    endpoint_per_second = int(dataset_size // (time_taken + 0.01))  # avoid 0 division
    timer_update = gr.Markdown.update(value=f'### 🔗 URI Analysis Results **| Time taken - {time_taken:.3f} seconds || '
                                            f'{endpoint_per_second} endpoints/s**, **{len(sorted_clusters)}** clusters')
    template_dropdown_update = gr.Dropdown.update(choices=cluster_templates)
    return printed_tree_max1000, template_dropdown_update, sorted_clusters_without_regex, timer_update


with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown('# 🔥Welcome to the URIDrain Demo!🔥')
    with gr.Row(variant='compact'):
        with gr.Column():
            file_dataset = gr.File(label='Upload a txt file with endpoints on each line',
                                   file_count='single', file_types=['txt'])
        with gr.Column():
            sample_data_selector = gr.Dataset(components=[gr.Textbox(visible=False)],
                                              label="Text Dataset",
                                              samples=[
                                                  ["Endpoint100_trivial"],
                                                  ["Endpoint200_hard"],
                                                  ["Endpoint100_trivial_3k_repeat"],
                                                  ["Endpoint200_hard_3k_repeat"],
                                                  ['Endpoint100_trivial_500k_perf_bench'],
                                                  ['Endpoint100_counterexamples'],
                                              ],
                                              )
            # Shuffling dataset
            shuffle_checkbox = gr.Checkbox(label="🔀 Shuffle data based on random seed", value=False, interactive=True)
            random_seed_text_cell = gr.Textbox(label="🌱 Random seed (For shuffle)", value='42', interactive=True)
        with gr.Column():
            text1 = gr.Textbox(label="Newline Character (Used to split URIs to dataset rows)", value="\\n",
                               interactive=False)
            # TODO Add ntlk support to here
            drop1 = gr.Dropdown(["URIDrain-V1", "URIDrain-NLTK(NOT WORKING YET!!!)"],
                                label="Algorithm Variant", value="URIDrain-V1", interactive=False)
            run_button = gr.Button(label="Click to Start Analysis", value='🔥Run🔥')
            # reset_button = gr.Button(label="Reset Algorithm state", value='Reset')

        with gr.Column():
            description = gr.Markdown('### ⚙️ Settings are auto-tuned for now')
            slider0 = gr.Slider(label="Similarity Threshold (AUTO)", minimum=0, maximum=1, step=0.1,
                                value=0.5, interactive=False)
            slider1 = gr.Slider(label="Max tree depth (Fixed)", minimum=1, maximum=10, step=1, value=4,
                                interactive=False)
            slider2 = gr.Slider(label="Max cluster count (Fixed)", minimum=1, maximum=1024, step=1, value=1024,
                                interactive=False)

        with gr.Row():
            with gr.Column():
                table_preview_markdown = gr.Markdown("### 📜 Endpoints dataset (or input your own here!)")
                table_preview = gr.TextArea(interactive=True, show_copy_button=True,
                                            placeholder='/abc/123/cde/456foobar', show_label=True)


                def print_data(file, shuffle, seed):
                    if hasattr(file, 'name'):  # it's an upload
                        file_path = file.name
                        label = f'Using Your Uploaded Data {file_path}'
                    elif isinstance(file, list):  # it's a sample list of length 1                            
                        file_path = file[0] + '.txt'
                        label = f'Using Sample Data {file_path}'
                    else:
                        print(type(file), file)
                        raise gradio.Error('😵 Critical dataset reading error (contact author) 😵')

                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    with open(os.path.join(script_dir, file_path), encoding="utf-8") as f:
                        content = f.read()
                    if 'perf_bench' in file_path:
                        return gr.TextArea.update(
                            value=content,
                            interactive=True,
                            label=label,
                            show_label=True,
                            visible=False)
                    return gr.TextArea.update(
                        value=content,
                        interactive=True,
                        show_copy_button=True,
                        label=label,
                        show_label=True
                    )


                file_dataset.change(fn=print_data, inputs=[file_dataset, shuffle_checkbox, random_seed_text_cell],
                                    outputs=[table_preview])

                sample_data_selector.click(print_data,
                                           inputs=[sample_data_selector, shuffle_checkbox, random_seed_text_cell],
                                           outputs=[table_preview])
    options = ['Placeholder (CLICK RUN FIRST!)']
    template_selector = gr.Dropdown(choices=options, label="Choose a template (🔽 sorted by size)",
                                    info='Evaluate the algorithm results')

    with gr.Row(equal_height=True):
        with gr.Column():
            analysis_results_markdown = gr.Markdown("### 🔗 URI Analysis Results")

            out_tree_text_cell = gr.Textbox(label='URI Parse Tree', interactive=False,
                                            show_copy_button=True, max_lines=75)
        with gr.Column():
            gr.Markdown("### 🔗 URI <--> 🔥Template Mapping (Choose one from dropdown)")

            out_template_endpoint_cell = gr.Textbox(label='Endpoints belonging to this template',
                                                    interactive=False, show_copy_button=True, max_lines=50)


            def populate_dropdown(selected_template):
                cluster_id_selected = int(selected_template.split('::')[0])
                global uri_to_cluster
                uris = uri_to_cluster[str(cluster_id_selected)]
                print(f'Extracting uris for cluster {cluster_id_selected}, size {len(uris)}')
                return '\n'.join(uris)


            template_selector.select(fn=populate_dropdown,
                                     inputs=[template_selector], outputs=[out_template_endpoint_cell])
    gr.HTML(back_to_top_btn_html)


    def update_shuffle_state(shuffle, seed):
        return gr.Markdown.update(value=f'### 📜 Endpoints dataset (Or input your own here!) '
                                        f'**Data is {"" if shuffle else "NOT"}🔀shuffled (seed {seed})!**')


    # Show clusters in another way
    gr.Markdown("### 🔗 Sorted Clusters and Extracted REGEX")

    cluster_text_cell = gr.TextArea(interactive=False, show_copy_button=True,
                                    label='🔽 Sorted by size and length (p_N is match group)')

    shuffle_checkbox.select(update_shuffle_state, inputs=[shuffle_checkbox, random_seed_text_cell],
                            outputs=[table_preview_markdown])
    run_button.click(cluster_uris, inputs=[table_preview, shuffle_checkbox, random_seed_text_cell],
                     outputs=[out_tree_text_cell, template_selector, cluster_text_cell, analysis_results_markdown])

auth = ('skywalking', 'skywalking')
# server_name='localhost',
demo.queue().launch(server_port=8080, share=False)

# iface.launch()
