# SPDX-License-Identifier: MIT

import ast
import configparser
import json
import logging
import os
import re

from models.uri_drain.masking import MaskingInstruction

logger = logging.getLogger(__name__)

env_regular_regex = re.compile(r'\${(?P<ENV>[_A-Z0-9]+):(?P<DEF>.*)}')


class TemplateMinerConfig:
    def __init__(self):
        self.engine = "Drain"
        self.profiling_enabled = False
        self.profiling_report_sec = 60
        self.snapshot_interval_minutes = 5
        self.snapshot_compress_state = True
        self.snapshot_file_dir = None
        self.drain_extra_delimiters = []
        self.drain_sim_th = 0.4
        self.drain_depth = 4
        self.drain_max_children = 100
        self.drain_max_clusters = None
        self.drain_analysis_min_url_count = 20
        self.masking_instructions = []
        self.mask_prefix = "<"
        self.mask_suffix = ">"
        self.parameter_extraction_cache_capacity = 3000
        self.parametrize_numeric_tokens = True

    def load(self, config_filename: str):
        parser = configparser.ConfigParser()
        read_files = parser.read(config_filename)
        if len(read_files) == 0:
            logger.warning(f"config file not found: {config_filename}")

        section_profiling = 'PROFILING'
        section_snapshot = 'SNAPSHOT'
        section_drain = 'DRAIN'
        section_masking = 'MASKING'

        self.engine = self.read_config_value(parser, section_drain, 'engine', str, self.engine)

        self.profiling_enabled = self.read_config_value(parser, section_profiling, 'enabled', bool,
                                                        self.profiling_enabled)
        self.profiling_report_sec = self.read_config_value(parser, section_profiling, 'report_sec', int,
                                                           self.profiling_report_sec)

        self.snapshot_interval_minutes = self.read_config_value(parser, section_snapshot, 'snapshot_interval_minutes',
                                                                int, self.snapshot_interval_minutes)
        self.snapshot_compress_state = self.read_config_value(parser, section_snapshot, 'compress_state', bool,
                                                              self.snapshot_compress_state)
        file_path = self.read_config_value(parser, section_snapshot, 'file_path', str, None)
        if file_path:
            self.snapshot_file_dir = file_path

        drain_extra_delimiters_str = self.read_config_value(parser, section_drain, 'extra_delimiters', str,
                                                            str(self.drain_extra_delimiters))
        self.drain_extra_delimiters = ast.literal_eval(drain_extra_delimiters_str)

        self.drain_sim_th = self.read_config_value(parser, section_drain, 'sim_th', float, self.drain_sim_th)
        self.drain_depth = self.read_config_value(parser, section_drain, 'depth', int, self.drain_depth)
        self.drain_max_children = self.read_config_value(parser, section_drain, 'max_children', int,
                                                         self.drain_max_children)
        self.drain_max_clusters = self.read_config_value(parser, section_drain, 'max_clusters', int,
                                                         self.drain_max_clusters)
        self.parametrize_numeric_tokens = self.read_config_value(parser, section_drain, 'parametrize_numeric_tokens',
                                                                 bool, self.parametrize_numeric_tokens)

        masking_instructions_str = self.read_config_value(parser, section_masking, 'masking', str,
                                                          str(self.masking_instructions))
        self.mask_prefix = self.read_config_value(parser, section_masking, 'mask_prefix', str, self.mask_prefix)
        self.mask_suffix = self.read_config_value(parser, section_masking, 'mask_suffix', str, self.mask_suffix)
        self.parameter_extraction_cache_capacity = self.read_config_value(parser, section_masking,
                                                                          'parameter_extraction_cache_capacity', int,
                                                                          self.parameter_extraction_cache_capacity)
        self.drain_analysis_min_url_count = self.read_config_value(parser, section_drain, 'analysis_min_url_count', int,
                                                                   self.drain_analysis_min_url_count)

        masking_instructions = []
        masking_list = json.loads(masking_instructions_str)
        for mi in masking_list:
            instruction = MaskingInstruction(mi['regex_pattern'], mi['mask_with'])
            masking_instructions.append(instruction)
        self.masking_instructions = masking_instructions

    def read_value_with_env(self, value: str):
        match = env_regular_regex.match(value)
        if match:
            env = match.group('ENV')
            default = match.group('DEF')
            return os.getenv(env, default)
        else:
            return value

    def read_config_value(self, parser, section, key, tp, default):
        conf_value = parser.get(section, key, fallback=None)
        if conf_value is None:
            return default
        val = self.read_value_with_env(conf_value)
        if tp == bool:
            if val.lower() not in parser.BOOLEAN_STATES:
                raise ValueError(f'Not a boolean: {val}')
            return parser.BOOLEAN_STATES[val.lower()]
        return tp(val)
