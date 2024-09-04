# SPDX-License-Identifier: MIT
# This file implements the Drain algorithm for log parsing.
# Based on https://github.com/logpai/logparser/blob/master/logparser/Drain/Drain.py by LogPAI team
# Again, it's further modified to suit URI clustering needs,
# changes are kept minimal to avoid divergence from Drain3 upstream.
# TODO Note:: Every change to upstream Drain3 algorithm MUST be commented starting with "Modified::"
import re
from typing import List, Dict, Sequence

from cachetools import LRUCache, Cache

from models.utils.simple_profiler import Profiler, NullProfiler

from textblob import TextBlob

import logger


class LogCluster:  # TODO Modified:: Changed to URICluster
    __slots__ = ["log_template_tokens", "cluster_id", "size", "latest_urls"]

    def __init__(self, log_template_tokens: list, cluster_id: int, combine_min_url_count: int):
        self.log_template_tokens = tuple(log_template_tokens)
        self.cluster_id = cluster_id
        self.size = 1
        self.latest_urls = LRUCache(combine_min_url_count+1)

    def get_template(self):
        # Modified:: Changed to join by slash instead of space for
        # Also special case considered for domain.top_level_domain or
        # www.domain.top_level_domain or http(s)://domain.top_level_domain
        # or http(s)://user:password@www.domain.top_level_domain
        # REASONING:: domain can only appear in the first two tokens, so whenever a dot appears, it must be a domain?
        # Another part of domain handling is done in create_template when they are hiding behind http(s)://
        first_token = self.log_template_tokens[0]
        if ':' in first_token:  # It's a URI scheme!
            scheme = first_token
            path = '/'.join(self.log_template_tokens[1:])
            # TODO: put this into the config file
            http_methods = ('OPTIONS', 'GET', 'HEAD', 'PUT', 'POST', 'DELETE', 'PATCH', 'TRACE', 'CONNECT')
            if scheme.startswith(http_methods):
                template = f"{scheme}/{path}"
            else:
                template = f"{scheme}//{path}"

            return template
        elif first_token[0].isupper() or '.' in first_token:  # It's something like HikariCP/Connection/getConnection
            return '/'.join(self.log_template_tokens)
        else:
            template = '/'.join(self.log_template_tokens)
            return f'/{template}'

    def adding_url(self, url: str):
        if self.latest_urls.__contains__(url):
            return
        self.latest_urls[url] = True

    def __str__(self):
        # return f"ID={str(self.cluster_id).ljust(5)} : size={str(self.size).ljust(10)}: {self.get_template()}"
        return f"size={str(self.size).ljust(10)}: {self.get_template()}"


class SingleURILogCluster:
    __slots__ = ["uri", "cluster_id", "size"]

    def __init__(self, uri: str):
        self.uri = uri
        self.cluster_id = -1
        self.size = 1

    def get_template(self):
        return self.uri

    def __str__(self):
        # return f"ID={str(self.cluster_id).ljust(5)} : size={str(self.size).ljust(10)}: {self.get_template()}"
        return f"size={str(self.size).ljust(10)}: {self.get_template()}"


class LogClusterCache(LRUCache):  # TODO Modified:: Changed to URICluster
    """
    Least Recently Used (LRU) cache which allows callers to conditionally skip
    cache eviction algorithm when accessing elements.
    """

    def __missing__(self, key):
        return None

    def get(self, key):
        """
        Returns the value of the item with the specified key without updating
        the cache eviction algorithm.
        """
        return Cache.__getitem__(self, key)


class Node:
    __slots__ = ["key_to_child_node", "cluster_ids"]

    def __init__(self):
        self.key_to_child_node: Dict[str, Node] = {}
        self.cluster_ids: List[int] = []


class DrainBase:
    def __init__(self,
                 depth=4,
                 sim_th=0.4,
                 max_children=100,
                 max_clusters=None,
                 combine_min_url_count=8,
                 extra_delimiters=(),
                 profiler: Profiler = NullProfiler(),
                 param_str="{var}",  # Modified:: required param_str
                 # param_extra=None,  # Modified:: Added param_extra
                 parametrize_numeric_tokens=True):
        """
        Create a new Drain instance.

        :param depth: max depth levels of log clusters. Minimum is 2.
            For example, for depth==4, Root is considered depth level 1.
            Token count is considered depth level 2.
            First log token is considered depth level 3.
            Log clusters below first token node are considered depth level 4.
        :param sim_th: similarity threshold - if percentage of similar tokens for a log message is below this
            number, a new log cluster will be created.
        :param max_children: max number of children of an internal node
        :param max_clusters: max number of tracked clusters (unlimited by default).
            When this number is reached, model starts replacing old clusters
            with a new ones according to the LRU policy.
        :param extra_delimiters: delimiters to apply when splitting log message into words (in addition to whitespace).
        :param parametrize_numeric_tokens: whether to treat tokens that contains at least one digit
            as template parameters.
        """
        # if param_extra is None:
        #     param_extra = {}
        if depth < 3:
            raise ValueError("depth argument must be at least 3")
        self.logger = logger.init_logger(logging_level='DEBUG', name='URIDrainV1')

        self.log_cluster_depth = depth
        self.max_node_depth = depth - 2  # max depth of a prefix tree node, starting from zero
        self.sim_th = sim_th
        self.max_children = max_children
        self.combine_min_url_count = combine_min_url_count
        self.root_node = Node()
        self.profiler = profiler
        self.extra_delimiters = extra_delimiters
        self.max_clusters = max_clusters
        self.param_str = param_str
        # MODIFIED:: Added param_extra
        # self.param_extra = param_extra
        # MODIFIED:: extract this to drain.attributes same as sequence similarity method needs this
        # self.possible_params = [self.param_extra['INT'], self.param_extra['STR'], self.param_extra['VAR']]
        self.parametrize_numeric_tokens = parametrize_numeric_tokens

        # key: int, value: LogCluster
        self.id_to_cluster = {} if max_clusters is None else LogClusterCache(maxsize=max_clusters)
        self.clusters_counter = 0

    @property
    def clusters(self):
        result = []
        for cluster in self.id_to_cluster.values():
            if cluster.latest_urls and cluster.latest_urls.__len__() >= self.combine_min_url_count:
                result.append(cluster)
                continue
            for url, _ in cluster.latest_urls.items():
                result.append(SingleURILogCluster(url))
        return result

    @property
    def cluster_patterns(self):
        sorted_drain_clusters = sorted(self.clusters, key=lambda it: it.size, reverse=True)
        return [cluster.get_template() for cluster in sorted_drain_clusters]

    @staticmethod
    def has_numbers(s):
        return any(char.isdigit() for char in s)

    def fast_match(self, cluster_ids: Sequence, tokens: list, sim_th: float, include_params: bool):
        """
        Find the best match for a log message (represented as tokens) versus a list of clusters
        :param cluster_ids: List of clusters to match against (represented by their IDs)
        :param tokens: the log message, separated to tokens.
        :param sim_th: minimum required similarity threshold (None will be returned in no clusters reached it)
        :param include_params: consider tokens matched to wildcard parameters in similarity threshold.
        :return: Best match cluster or None
        """
        # MODIFIED:: Changed to use URI cluster
        # get number of tokens that contain digits
        digit_tokens = [token for token in tokens if self.has_numbers(token)]

        digit_count = len(digit_tokens)
        # MODIFIED:: Taken from DAGDrain paper
        sim_th = 0.5 * ((len(tokens) - digit_count) / len(tokens))

        match_cluster = None

        max_sim = -1
        max_param_count = -1
        max_cluster = None

        for cluster_id in cluster_ids:
            # Try to retrieve cluster from cache with bypassing eviction
            # algorithm as we are only testing candidates for a match.
            cluster = self.id_to_cluster.get(cluster_id)
            if cluster is None:
                continue
            cur_sim, param_count = self.get_seq_distance(cluster.log_template_tokens, tokens, include_params)
            # self.logger.debug(f'SIMILARITY = {cur_sim} for c{cluster_id}, {cluster.log_template_tokens} param={param_count}')
            if cur_sim > max_sim or (cur_sim == max_sim and param_count > max_param_count):
                # todo: this is known caveat
                # MODIFIED:: Preceding domain should always be the same (Actual code modified in get_seq_distance)
                # print( f'cur_sim = {cur_sim}, param_count = {param_count}, max_sim = {max_sim}, max_param_count = {
                # max_param_count}')
                max_sim = cur_sim
                max_param_count = param_count
                max_cluster = cluster

        if max_sim >= sim_th:
            match_cluster = max_cluster

        return match_cluster

    def print_tree(self, file=None, max_clusters=5):
        self.print_node("root", self.root_node, 0, file, max_clusters)

    def print_node(self, token, node, depth, file, max_clusters):
        out_str = '\t' * depth

        if depth == 0:
            out_str += f'<{token}>'
        elif depth == 1:
            if token.isdigit():
                out_str += f'<L={token}>'
            else:
                out_str += f'<{token}>'
        else:
            out_str += f'"{token}"'

        if len(node.cluster_ids) > 0:
            out_str += f" (cluster_count={len(node.cluster_ids)})"

        print(out_str, file=file)

        for token, child in node.key_to_child_node.items():
            self.print_node(token, child, depth + 1, file, max_clusters)

        for cid in node.cluster_ids[:max_clusters]:
            cluster = self.id_to_cluster[cid]
            out_str = '\t' * (depth + 1) + str(cluster)
            print(out_str, file=file)

    def get_content_as_tokens(self, content):
        content = content.strip()
        for delimiter in self.extra_delimiters:
            content = content.replace(delimiter, " ")
        content_tokens = content.split()
        return content_tokens

    def add_log_message(self, content: str):
        """
        TODO MODIFIED:: Entirely modified
        :param content:
        :return:
        """
        content_tokens = self.get_content_as_tokens(content)

        if self.profiler:
            self.profiler.start_section("tree_search")
        match_cluster = self.tree_search(self.root_node, content_tokens, self.sim_th, False)
        if self.profiler:
            self.profiler.end_section()

        # Match no existing log cluster
        if match_cluster is None:
            if self.profiler:
                self.profiler.start_section("create_cluster")
            self.clusters_counter += 1
            cluster_id = self.clusters_counter
            match_cluster = LogCluster(content_tokens, cluster_id, self.combine_min_url_count)
            self.id_to_cluster[cluster_id] = match_cluster
            self.add_seq_to_prefix_tree(self.root_node, match_cluster)
            update_type = "cluster_created"

        # Add the new log message to the existing cluster
        else:
            if self.profiler:
                self.profiler.start_section("cluster_exist")
            new_template_tokens = self.create_template(content_tokens, match_cluster.log_template_tokens)
            if new_template_tokens == "rejected":
                # self.logger.debug(f'template reuse rejected for content_tokens = {content_tokens} ')
                # added, it should be new template tokens
                update_type = "rejected (create new)"
                self.clusters_counter += 1
                cluster_id = self.clusters_counter
                match_cluster = LogCluster(content_tokens, cluster_id, self.combine_min_url_count)
                self.id_to_cluster[cluster_id] = match_cluster
                self.add_seq_to_prefix_tree(self.root_node, match_cluster)
                match_cluster.size -= 1
            elif tuple(new_template_tokens) == match_cluster.log_template_tokens:
                update_type = "none"
            else:
                match_cluster.log_template_tokens = tuple(new_template_tokens)
                update_type = "cluster_template_changed"
            match_cluster.size += 1
            # Touch cluster to update its state in the cache.
            # noinspection PyStatementEffect
            self.id_to_cluster[match_cluster.cluster_id]

        if self.profiler:
            self.profiler.end_section()

        match_cluster.adding_url(content)
        return match_cluster, update_type

    def get_total_cluster_size(self):
        size = 0
        for c in self.id_to_cluster.values():
            size += c.size
        return size

    def get_clusters_ids_for_seq_len(self, seq_fir):
        """
        seq_fir: int/str - the first token of the sequence
        Return all clusters with the specified count of tokens
        """

        def append_clusters_recursive(node: Node, id_list_to_fill: list):
            id_list_to_fill.extend(node.cluster_ids)
            for child_node in node.key_to_child_node.values():
                append_clusters_recursive(child_node, id_list_to_fill)

        cur_node = self.root_node.key_to_child_node.get(str(seq_fir))

        # no template with same token count
        if cur_node is None:
            return []

        target = []
        append_clusters_recursive(cur_node, target)
        return target


class Drain(DrainBase):

    def __init__(self,
                 depth=4,
                 sim_th=0.4,
                 max_children=100,
                 max_clusters=None,
                 combine_min_url_count=8,
                 extra_delimiters=(),
                 profiler: Profiler = NullProfiler(),
                 param_str="<*>",
                 # param_extra=None,  # Modified:: Added param_extra
                 parametrize_numeric_tokens=True):
        super().__init__(depth, sim_th, max_children, max_clusters, combine_min_url_count, extra_delimiters, profiler, param_str,
                         # param_extra,
                         parametrize_numeric_tokens)

    def tree_search(self, root_node: Node, tokens: list, sim_th: float, include_params: bool):

        # at first level, children are grouped by token (word) count
        token_count = len(tokens)
        cur_node = root_node.key_to_child_node.get(str(token_count))

        # no template with same token count yet
        if cur_node is None:
            return None

        # handle case of empty log string - return the single cluster in that group
        if token_count == 0:
            return self.id_to_cluster.get(cur_node.cluster_ids[0])

        # find the leaf node for this log - a path of nodes matching the first N tokens (N=tree depth)
        cur_node_depth = 1
        for token in tokens:
            # at max depth
            if cur_node_depth >= self.max_node_depth:
                break

            # this is last token
            if cur_node_depth == token_count:
                break

            key_to_child_node = cur_node.key_to_child_node
            cur_node = key_to_child_node.get(token)
            if cur_node is None:  # no exact next token exist, try wildcard node
                cur_node = key_to_child_node.get(self.param_str)
            if cur_node is None:  # no wildcard node exist
                return None

            cur_node_depth += 1

        # get best match among all clusters with same prefix, or None if no match is above sim_th
        cluster = self.fast_match(cur_node.cluster_ids, tokens, sim_th, include_params)
        # FIXME MODIFIED:: print for debugging
        # #self.logger.debug("cluster: ", cluster)
        return cluster

    def add_seq_to_prefix_tree(self, root_node, cluster: LogCluster):
        token_count = len(cluster.log_template_tokens)
        token_count_str = str(token_count)
        if token_count_str not in root_node.key_to_child_node:
            first_layer_node = Node()
            root_node.key_to_child_node[token_count_str] = first_layer_node
        else:
            first_layer_node = root_node.key_to_child_node[token_count_str]

        cur_node = first_layer_node

        # handle case of empty log string
        if token_count == 0:
            cur_node.cluster_ids = [cluster.cluster_id]
            return

        current_depth = 1
        for token in cluster.log_template_tokens:

            # if at max depth or this is last token in template - add current log cluster to the leaf node
            if current_depth >= self.max_node_depth or current_depth >= token_count:
                # clean up stale clusters before adding a new one.
                new_cluster_ids = []
                for cluster_id in cur_node.cluster_ids:
                    if cluster_id in self.id_to_cluster:
                        new_cluster_ids.append(cluster_id)
                new_cluster_ids.append(cluster.cluster_id)
                cur_node.cluster_ids = new_cluster_ids
                break

            # if token not matched in this layer of existing tree.
            if token not in cur_node.key_to_child_node:
                # MODIFIED:: This is not needed since domain can contain digits
                # WE SHOULD DO NOTHING SO OVERRIDING THE SETTING
                self.parametrize_numeric_tokens = False
                if self.parametrize_numeric_tokens and self.has_numbers(token):
                    if self.param_str not in cur_node.key_to_child_node:
                        new_node = Node()
                        cur_node.key_to_child_node[self.param_str] = new_node
                        cur_node = new_node
                    else:
                        cur_node = cur_node.key_to_child_node[self.param_str]

                else:
                    if self.param_str in cur_node.key_to_child_node:
                        if len(cur_node.key_to_child_node) < self.max_children:
                            new_node = Node()
                            cur_node.key_to_child_node[token] = new_node
                            cur_node = new_node
                        else:
                            cur_node = cur_node.key_to_child_node[self.param_str]
                    else:
                        if len(cur_node.key_to_child_node) + 1 < self.max_children:
                            new_node = Node()
                            cur_node.key_to_child_node[token] = new_node
                            cur_node = new_node
                        elif len(cur_node.key_to_child_node) + 1 == self.max_children:
                            new_node = Node()
                            cur_node.key_to_child_node[self.param_str] = new_node
                            cur_node = new_node
                        else:
                            cur_node = cur_node.key_to_child_node[self.param_str]

            # if the token is matched
            else:
                cur_node = cur_node.key_to_child_node[token]

            current_depth += 1

    # seq1 is a template, seq2 is the log to match
    # FIXME MODIFIED:: entirely modified for URI matching include_params is false when add_logmessage
    def get_seq_distance(self, seq1, seq2, include_params: bool):
        """
        Todo this is modified to match uris
        Input (8): /api/v1/invoices/123abc456

        cur_sim = 0.5 for cluster 1, cluster.log_template_tokens = ('api', 'v777', 'orders', '123abc456')
        cur_sim = 0.5, param_count = 0, max_sim = -1, max_param_count = -1
        cur_sim = 0.5 for cluster 2, cluster.log_template_tokens = ('api', 'v1', 'accounts', 'xyz')
        cur_sim = 0.75 for cluster 3, cluster.log_template_tokens = ('api', 'v1', 'posts', '123abc456')
        cur_sim = 0.75, param_count = 0, max_sim = 0.5, max_param_count = 0
        cur_sim = 0.5 for cluster 4, cluster.log_template_tokens = ('api', 'v1', 'users', 'def')
        cur_sim = 0.75 for cluster 5, cluster.log_template_tokens = ('api', 'v1', 'invoices', 'abcxyz') <<< this should be chosen not posts one even if 0.75
        """
        assert len(seq1) == len(seq2)

        # sequences are empty - full match
        if len(seq1) == 0:
            return 1.0, 0

        sim_tokens = 0
        param_count = 0
        # TODO:: This needs a second thought
        # MODIFIED:: modified here to ensure domain is matched
        for index, (token1, token2) in enumerate(zip(seq1, seq2)):
            if (index == 0 or index == 1) and '.' in token1 and token1 != token2:
                # self.logger.debug('this is domain mismatch!')
                return 0.0, 0
            # if all new tokens are words, then we can consider it cannot be combined
            if token1 != token2 and (self.check_all_url_deep_correct(token2) or self.check_all_url_deep_correct(token1)):
                return -1, -1
            # if token1 in self.possible_params or token1 == self.param_str:
            if token1 == self.param_str:
                param_count += 1
                continue
            if token1 == token2:  # changed here 2023
                if token1.isdigit() and token2.isdigit():  # this is edge case where template is very new and has digits
                    sim_tokens += 0.5  # FIXME This maybe tricky to tune, and do we consider token2 or just token1
                elif token1.isalpha():
                    sim_tokens += 1
                else:
                    sim_tokens += 1
        if include_params:
            sim_tokens += param_count

        ret_val = float(sim_tokens) / len(seq1)
        return ret_val, param_count

    def split_for_url(self, text):
        # split text by camel case and digits
        pattern = r"(?<=[a-z])(?=[A-Z])|(?<=\d)(?=\D)|(?<=\D)(?=\d)"
        return re.split(pattern, text)

    def check_all_url_deep_correct(self, text):
        words = self.split_for_url(text)
        for word in self.split_for_url(text):
            # if contains digits, then it's not a word, ignore the word check
            if word.isdigit():
                return False
            # When a word is not corrected, then it's not a param
            # text blob would also split the world by regex `\w+`, so no worry about special characters(such as "_", ".")
            corrected_word = TextBlob(word).correct()
            if word != corrected_word:
                return False

        return True

    def create_template(self, seq1, seq2):
        # MODIFIED::
        assert len(seq1) == len(seq2)
        ret_val = list(seq2)
        seq_length = len(seq1)

        # TODO, radical assumption if there's absolutely 0 digit in seq1 and seq2, then don't consider them similar?
        # To implement this, we increase the false negative rate, but decrease false positive rate

        for i, (token1, token2) in enumerate(zip(seq1, seq2)):
            pre_token = ret_val[i - 1] if i > 0 else None
            sub_token = ret_val[i + 1] if i < len(ret_val) - 1 else None
            if token1 != token2:
                if seq_length == 1:  # if an uri is of length 1 then it must not share any similarity with any template
                    return 'rejected'
                if seq_length == 2:
                    # This is to handle cases of
                    # [0]same_domain/[1]FIRST_ACTUAL_TOKEN or
                    # here we assume that FIRST_ACTUAL_TOKEN is not a param,
                    # so we safely reject if they don't match
                    if i == 1 and '.' in pre_token:
                        return 'rejected'
                if seq_length == 3:
                    # [0]scheme://[1]same_domain/[2]FIRST_ACTUAL_TOKEN,
                    if i == 2 and '.' in pre_token:
                        return 'rejected'
                # First handle domains in uri
                if i == 1 and ':' in pre_token:  # it means domain mismatch
                    # [0]scheme://[1]same_domain/[2]FIRST_ACTUAL_TOKEN,
                    # self.logger.debug(f'pre_token = {pre_token}, matched cluster = {seq2}')
                    # TODO Check: handled in similarity check, remove this ^^^
                    # I assume domain can only appear in either first or second token
                    # domain unhandled can only appear in second token
                    # (scheme://abc:123@blabla.domain.top_level_domain/...)
                    # first token domain is already handled by drain3 since it exact matches first token
                    return 'rejected'
                # self.logger.debug(f'seq1 (incoming uri) = {"/".join(seq1)}')
                # self.logger.debug(f'seq2 (matched template) = {"/".join(seq2)}')
                # TODO These checks are not perfect, but they are good, only very edge cases will trigger a problem
                # TODO The edge case is when update/123 appears and no other update/xxx appears, then it will not think
                # TODO that xxx is a param, causing further endpoints looks like it to think the "update" is a param
                # TODO it's already mostly avoided since there almost always is a subsequent token that is param which
                # TODO will cause lead the entire update to be rejected (REASONING)
                # A fix maybe add weight to integer tokens
                """/api-this-is-a-special-case/v99999999999999999/orders/update/123
                /api-this-is-a-special-case/v99999999999999999/orders/update/456
                /api-this-is-a-special-case/v99999999999999999/orders/update/12222224444
                /api-this-is-a-special-case/v99999999999999999/orders/update/122222222222222222222222
                /api-this-is-a-special-case/v99999999999999999/orders/delete/12222222222222222244
                /api-this-is-a-special-case/v99999999999999999/orders/delete/12
                /api-this-is-a-special-case/v99999999999999999/orders/reorder/122222222222222464643
                /api-this-is-a-special-case/v99999999999999999/orders/reorder/1222222222222221111111 rejected for
                content_tokens = ['api-this-is-a-special-case', 'v99999999999999999', 'orders', 'delete',
                '12222222222222222244'] sub_token is param_str, so current token cannot be a param (assumption) rejected for
                content_tokens = ['api-this-is-a-special-case', 'v99999999999999999', 'orders', 'reorder',
                '122222222222222464643']"""

                # REASONING:: This is a useful side effect,
                # Since we change ret_val in each iteration, so when we appear to get two
                # consecutive tokens that are params ->
                # Something must be wrong! So we simply reject and return a new template instead of changing old one.
                """working on token 12222222222222222244 and 123, index 4 pre_token <:STR:> is param_str,
                so current token cannot be a param (assumption) tokens of sequence2 = ('api-this-is-a-special-case', 'v99999999999999999',
                'orders', 'update', '123') rejected for content_tokens = ['api-this-is-a-special-case',
                'v99999999999999999', 'orders', 'delete', '12222222222222222244'] working on token
                122222222222222464643 and 123, index 4 pre_token <:STR:> is param_str, so current token cannot be a param (assumption)
                tokens of sequence2 = ('api-this-is-a-special-case', 'v99999999999999999', 'orders', 'update',
                '123') rejected for content_tokens = ['api-this-is-a-special-case', 'v99999999999999999', 'orders',
                'reorder', '122222222222222464643']"""

                # ASSUMPTION: There cannot be two consecutive params
                if pre_token == self.param_str:  # or pre_token in self.possible_params:
                    # self.logger.debug(f'working on token {token1} and {token2}, index {i}')
                    # self.logger.debug(f'pre_token {pre_token} is param_str, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"
                if sub_token == self.param_str:  # or sub_token in self.possible_params:
                    # self.logger.debug(f'sub_token {sub_token} is param_str, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"
                # ASSUMPTION: A subsequent token to version number cannot be a param
                if pre_token is not None and pre_token.startswith(
                        'v') and pre_token[1:].isdigit():
                    # self.logger.debug('pre_token is a version number, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"
                if token1.startswith('v') and token1[1:].isdigit():
                    # self.logger.debug('token1 is a version number, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"
                if pre_token and self.has_numbers(pre_token):
                    # Based on assumption that no two consecutive tokens can be params
                    # So attempt to change this position must ensure that the previous token is not a param
                    # self.logger.debug('pre_token has numbers, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"
                if sub_token and self.has_numbers(sub_token):
                    # Based on assumption that no two consecutive tokens can be params
                    # So attempt to change this position must ensure that the subsequent token is not a param
                    # self.logger.debug('sub_token has numbers, so current token cannot be a param (assumption)')
                    # self.logger.debug(f'tokens of sequence2 = {seq2}')
                    return "rejected"

                ret_val[i] = self.param_str

        # self.logger.debug(f'After change: {ret_val}')
        return ret_val

    def match(self, content: str, full_search_strategy="never"):
        """
        Match log message against an already existing cluster.
        Match shall be perfect (sim_th=1.0).
        New cluster will not be created as a result of this call, nor any cluster modifications.

        :param content: log message to match
        :param full_search_strategy: when to perform full cluster search.
            (1) "never" is the fastest, will always perform a tree search [O(log(n)] but might produce
            false negatives (wrong mismatches) on some edge cases;
            (2) "fallback" will perform a linear search [O(n)] among all clusters with the same token count, but only in
            case tree search found no match.
            It should not have false negatives, however tree-search may find a non-optimal match with
            more wildcard parameters than necessary;
            (3) "always" is the slowest. It will select the best match among all known clusters, by always evaluating
            all clusters with the same token count, and selecting the cluster with perfect all token match and least
            count of wildcard matches.
        :return: Matched cluster or None if no match found.
        """

        assert full_search_strategy in ["always", "never", "fallback"]

        required_sim_th = 1.0
        content_tokens = self.get_content_as_tokens(content)

        # consider for future improvement:
        # It is possible to implement a recursive tree_search (first try exact token match and fallback to
        # wildcard match). This will be both accurate and more efficient than the linear full search
        # also fast match can be optimized when exact match is required by early
        # quitting on less than exact cluster matches.
        def full_search():
            all_ids = self.get_clusters_ids_for_seq_len(len(content_tokens))
            cluster = self.fast_match(all_ids, content_tokens, required_sim_th, include_params=True)
            return cluster

        if full_search_strategy == "always":
            return full_search()

        match_cluster = self.tree_search(self.root_node, content_tokens, required_sim_th, include_params=True)
        if match_cluster is not None:
            return match_cluster

        if full_search_strategy == "never":
            return None

        return full_search()
