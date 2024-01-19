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
[WORK IN PROGRESS] TODO: implement post drain steps
This module is used for postprocessing of BATCH jobs, the reasoning is explained below:

When there are size 1 clusters or clusters WITHOUT ANY <:???:> masked symbols,
we utilize NLTK and Inflect to do lexical analysis to "guess" regex for them.

Example: Size=1, template=users/abc123/posts/p123091/update
Further parsed: WORD/NON_WORD/WORD/NON_WORD/WORD

Also when theres a variable identified, its not possible to have another variable consectively, although two path segments
can occur together.
"""
# TODO: CHECK MEMORY USAGE!

nltk_enabled = True
if nltk_enabled:
    import nltk
    import inflect

    p = inflect.engine()
    nltk.download('words')
    from nltk.corpus import words

    set_of_words = set(words.words())


def test_is_english_word(word):
    word = word.lower()
    word = p.singular_noun(word) if p.singular_noun(word) else word
    print(f'checking word: {word}')
    if word in set_of_words:
        return True
    else:
        return False


if __name__ == '__main__':
    test_targets = ['api/v2/data/users/def/hihihi', 'users/abc123/posts/123091/update']
    for test_target in test_targets:
        for word in test_target.split('/'):
            print(test_is_english_word(word))
