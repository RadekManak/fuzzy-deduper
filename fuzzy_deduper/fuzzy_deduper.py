#!/usr/bin/env python3
"""Find similar functions in python projects using edit distance."""
import sys
import tokenize
import glob
from fuzzywuzzy import fuzz


class TokenizedFunction:
    """For storing function information. Represents one function in a file."""

    def __init__(self, file_url, def_token, parsed_tokens):
        """Initialize object variables."""
        parsed_header = parse_function_header(parsed_tokens)
        self.tokens = parsed_tokens
        self.file_url = file_url
        self.line = def_token.start[0]
        self.name = parsed_header[0]
        self.args = parsed_header[1]
        self.kw_count = count_keywords(parsed_tokens)

    def similarity_ratio(self, tokenized_function) -> int:
        """Use edit distance to calculate similarity ratio.

        :returns similarity in percentage integer
        """
        token_word_a = create_token_type_word(self.tokens)
        token_word_b = create_token_type_word(tokenized_function.tokens)
        return fuzz.ratio(token_word_a, token_word_b)


KW_DICT = {'and': 'Ұ', 'del': 'ұ', 'from': 'Ҳ', 'not': 'ҳ', 'while': 'Ҵ',
           'as': 'ҵ', 'elif': 'Ҷ', 'global': 'ҷ', 'or': 'Ҹ', 'with': 'ҹ',
           'assert': 'Һ', 'else': 'һ', 'if': 'Ҽ', 'pass': 'ҽ', 'yield': 'Ҿ',
           'break': 'ҿ', 'except': 'Ӏ', 'import': 'Ӂ', 'print': 'ӂ',
           'class': 'Ӄ', 'exec': 'ӄ', 'in': 'Ӆ', 'raise': 'ӆ', 'continue': 'Ӈ',
           'finally': 'ӈ', 'is': 'Ӊ', 'return': 'ӊ', 'def': 'Ӌ', 'for': 'ӌ',
           'lambda': 'Ӎ', 'try': 'ӎ', }


def load_functions(url: str):
    """
    Recursively calls parse_functions on each file.

    :param url: file or directory
    :return: TokenizedFunction generator
    """
    file_list = []
    if url.endswith('.py'):
        file_list.append(url)
    else:
        file_list = glob.iglob(url + '/**/*.py', recursive=True)
    for filename in file_list:
        parsed_file = parse_functions(filename)
        for func in parsed_file:
            yield func


def parse_functions(url: str):
    """For each function in file creates TokenizedFunction object."""
    with open(url, 'rb') as file:
        tokenize_file = tokenize.tokenize(file.readline)
        functions = []
        indent = 0
        for token_info in tokenize_file:
            if indent == 0 and token_info.string == 'def':
                def_token = token_info
                parsed_tokens = []
                indent = -1
            elif indent == -1 and token_info.type == 5:
                indent = 2
            elif indent > 1 and token_info.type == 6:
                indent -= 1
            elif indent > 1 and token_info.type == 5:
                indent += 1
            if indent == 1 and token_info.type == 6:
                indent = 0
                parsed_tokens.append(token_info)
                function = TokenizedFunction(url, def_token, parsed_tokens)
                functions.append(function)
            if indent > 0 or indent == -1:
                parsed_tokens.append(token_info)
    return functions


def create_token_type_word(tokens):
    """
    Convert token types to characters.

    Keywords get it's own char to differentiate between them.
    """
    token_type_word = ''
    for token in tokens:
        if token.type == 1 and token.string in KW_DICT:
            token_type_word += KW_DICT[token.string]
        else:
            token_type_word += chr(token.type)
    return token_type_word


def count_keywords(function_tokens):
    """:returns number of keywords in function."""
    count = 0
    for token in function_tokens:
        if token.string in KW_DICT:
            count += 1
    return count


def parse_function_header(function_tokens):
    """
    Parse function name and its arguments from tokens.

    :param function_tokens:
    :return: [name(str), args(list)]
    """
    name = ''
    args = []
    state = 'start'
    for token in function_tokens:
        if token.string == 'def':
            state = 'name'
        elif state == 'skip_parenthesis':
            if token.string == ')':
                state = 'args'
        elif state == 'skip':
            if token.string == '(':
                state = 'skip_parenthesis'
            else:
                state = 'args'
        elif state == 'name':
            name = token.string
            state = 'args'
        elif token.string in {'\n', '(', ','}:
            pass
        elif token.string in {':', '='}:
            state = 'skip'
        elif token.string == ')':
            return [name, args]
        else:
            args.append(token.string)
    return None


def find_duplicates(tokenized_functions, min_similarity, min_kw_count):
    """
    Print similar functions.

    :param tokenized_functions: TokenizedFunction iterable
    :param min_similarity: minimum similarity ration in percentage
    :param min_kw_count functions with that have less keywords are ignored
    """
    seen = set()
    for afunction in tokenized_functions:
        for func in seen:
            similarity = afunction.similarity_ratio(func)
            if similarity >= min_similarity \
                    and func.kw_count >= min_kw_count \
                    and afunction.kw_count >= min_kw_count:
                print('-'*50)
                print(afunction.file_url, '|', afunction.name,
                      afunction.args, 'line:', str(afunction.line))
                print(func.file_url, '|', func.name,
                      func.args, 'line:', str(func.line))
                print('similarity ratio:', similarity)
        seen.add(afunction)


def main():
    """Parse input arguments."""
    if len(sys.argv) == 4:
        find_duplicates(load_functions(sys.argv[1]), int(sys.argv[2]),
                        int(sys.argv[3]))
    elif len(sys.argv) == 3:
        find_duplicates(load_functions(sys.argv[1]), int(sys.argv[2]), 4)
    elif len(sys.argv) == 2:
        find_duplicates(load_functions(sys.argv[1]), 85, 4)
    else:
        print('Usage: fuzzy_deduper.py <path-to-folder>'
              ' <min_similarity>[85] <min_kw_count>[4]')


if __name__ == '__main__':
    main()
