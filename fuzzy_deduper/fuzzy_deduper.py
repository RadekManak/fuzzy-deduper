#!/usr/bin/env python3
import sys
import tokenize
from fuzzywuzzy import fuzz
import glob


def load_functions(url: str):
    file_list = []
    if url.endswith('.py'):
        file_list.append(url)
    else:
        file_list = glob.iglob(url + '/**/*.py', recursive=True)
    for filename in file_list:
        parsed_file = parse_functions(filename)
        for func in parsed_file:
            yield func


kw_dict = {'and': 'Ұ', 'del': 'ұ', 'from': 'Ҳ', 'not': 'ҳ', 'while': 'Ҵ',
           'as': 'ҵ', 'elif': 'Ҷ', 'global': 'ҷ', 'or': 'Ҹ', 'with': 'ҹ',
           'assert': 'Һ', 'else': 'һ', 'if': 'Ҽ', 'pass': 'ҽ', 'yield': 'Ҿ',
           'break': 'ҿ', 'except': 'Ӏ', 'import': 'Ӂ', 'print': 'ӂ',
           'class': 'Ӄ', 'exec': 'ӄ', 'in': 'Ӆ', 'raise': 'ӆ', 'continue': 'Ӈ',
           'finally': 'ӈ', 'is': 'Ӊ', 'return': 'ӊ', 'def': 'Ӌ', 'for': 'ӌ',
           'lambda': 'Ӎ', 'try': 'ӎ', }


def parse_functions(url: str):
    with open(url, 'rb') as f:
        g = tokenize.tokenize(f.readline)
        functions = []
        indent = 0
        for tokenInfo in g:
            if indent == 0 and tokenInfo.string == 'def':
                def_token = tokenInfo
                parsed_tokens = []
                indent = -1
            elif indent == -1 and tokenInfo.type == 5:
                indent = 2
            elif indent > 1 and tokenInfo.type == 6:
                indent -= 1
            elif indent > 1 and tokenInfo.type == 5:
                indent += 1
            if indent == 1 and tokenInfo.type == 6:
                indent = 0
                parsed_tokens.append(tokenInfo)
                function = TokenizedFunction(url, def_token, parsed_tokens)
                functions.append(function)
            if indent > 0 or indent == -1:
                parsed_tokens.append(tokenInfo)
    return functions


class TokenizedFunction(object):

    def __init__(self, file_url, def_token, parsed_tokens):
        parsed_header = parse_function_header(parsed_tokens)
        self.tokens = parsed_tokens
        self.file_url = file_url
        self.line = def_token.start[0]
        self.name = parsed_header[0]
        self.args = parsed_header[1]
        self.kw_count = count_keywords(parsed_tokens)

    def __repr__(self):
        return repr(self.name) \
               + "(" + repr(self.args) + ")\n"

    def equals_name(self, tokenized_function) -> bool:
        """ True if functions have the same name"""
        return self.name == tokenized_function.name

    def similarity_ratio(self, tokenized_function):
        a = create_token_type_word(self.tokens)
        b = create_token_type_word(tokenized_function.tokens)
        return fuzz.ratio(a, b)

    def equals_params_name(self, tokenized_function) -> bool:
        """ True if functions have the same args regardless of order """
        if len(self.args) == len(tokenized_function.function_args):
            return len(set(self.args)
                       - set(tokenized_function.function_args)) == 0
        else:
            return False


def create_token_type_word(tokens):
    token_type_word = ''
    for token in tokens:
        if token.type == 1 and token.string in kw_dict:
            token_type_word += kw_dict[token.string]
        else:
            token_type_word += chr(token.type)
    return token_type_word


def count_keywords(function_tokens):
    count = 0
    for token in function_tokens:
        if token.string in kw_dict:
            count += 1
    return count


def parse_function_header(function_tokens):
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


def find_duplicates(tokenized_functions, min_similarity, min_kw_count):
    seen = set()
    for function in tokenized_functions:
        for func in seen:
            similarity = function.similarity_ratio(func)
            if similarity >= min_similarity \
                    and func.kw_count >= min_kw_count \
                    and function.kw_count >= min_kw_count:
                print('-'*50)
                print(function.file_url, '|', function.name,
                      function.args, 'line:', str(function.line))
                print(func.file_url, '|', func.name,
                      func.args, 'line:',  str(func.line))
                print('similarity ratio:', similarity)
        seen.add(function)


def main():
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
0