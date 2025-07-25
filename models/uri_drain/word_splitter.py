# Copyright 2023 SkyAPM org
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from cachetools import LRUCache
from spellchecker import SpellChecker

last_word_correct_lru = LRUCache(1000)
word_spell = SpellChecker()


def split_for_url(text):
    # split text by camel case
    pattern = r"(?<=[a-z])(?=[A-Z])"
    return re.split(pattern, text)


def check_all_word_correct(text):
    # if contains digits, then it's not a word, ignore the word check
    if any(char.isdigit() for char in text):
        return False
    for word in split_for_url(text):
        # if a word is too long, then it's not a word, just ignore to verify to reduce the analysis time
        if len(word) > 20:
            return False
        word = word.lower()
        cached_result = last_word_correct_lru.get(word)
        if cached_result is not None:
            if cached_result:
                continue
            else:
                return False
        correct = word in word_spell
        last_word_correct_lru[word] = correct
        if not correct:
            return False

    return True


def load_customized_words(path: str):
    if not path:
        return
    """
    Load custom words from a file and add them to the spell checker.
    Each line in the file should contain one word.
    """
    with open(path, 'r') as file:
        for line in file:
            # ignore the comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            word = line.strip()
            if word:  # Ensure the line is not empty
                word_spell.word_frequency.add(word.lower())
