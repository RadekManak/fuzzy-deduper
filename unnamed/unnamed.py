#!/usr/bin/env python3
import tokenize
from fuzzywuzzy import fuzz
import glob


def load_functions(url):
    for filename in glob.iglob(url + '/**/*.py', recursive=True):
        parsed_file = parse_functions(filename)
        for func in parsed_file:
            yield func


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
        self.flow_word = tokens_to_chars(filter_flow_tokens(self.tokens))

    def __repr__(self):
        return repr(self.name) \
               + "(" + repr(self.args) + ")\n"

    def equals_name(self, tokenized_function) -> bool:
        """ True if functions have the same name"""
        return self.name == tokenized_function.name

    def similarity_ratio(self, tokenized_function):
        return fuzz.ratio(self.flow_word, tokenized_function.flow_word)

    def equals_params_name(self, tokenized_function) -> bool:
        """ True if functions have the same args regardless of order """
        if len(self.args) == len(tokenized_function.function_args):
            return len(set(self.args)
                       - set(tokenized_function.function_args)) == 0
        else:
            return False


def filter_flow_tokens(function_tokens):
    allowed = {'with', 'for', 'if', 'elif', 'while', 'return', 'in', 'try', 'except'}
    filtered_tokens = []
    for token in function_tokens:
        if token.string in allowed:
            filtered_tokens.append(token)
    return filtered_tokens


def tokens_to_chars(filtered_tokens):
    func_word = ''
    dictionary = {'with': '0',
                  'for': '1',
                  'if': '2',
                  'elif': '3',
                  'while': '4',
                  'return': '5',
                  'in': '6',
                  'try': '7',
                  'except': '8'}
    for token in filtered_tokens:
        func_word += dictionary[token.string]
    return func_word


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


def find_duplicates(tokenized_functions, minimum):
    seen = set()
    for function in tokenized_functions:
        for func in seen:
            if function.similarity_ratio(func) >= minimum and len(function.flow_word) > 8 and len(func.flow_word) > 8:
                if function.name != '__init__':
                    print(function.file_url, function.name, function.line)
                    print(func.file_url, func.name, 'line:',  func.line)
                    print('similarity ratio', function.similarity_ratio(func))
                    print('-'*40)
        seen.add(function)


def main():
    if len(sys.argv) == 3:
        find_duplicates(load_functions(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 2:
        find_duplicates(load_functions(sys.argv[1]), 75)
    else:
        print('Usage: unnamed.py <path-to-folder>')


if __name__ == '__main__':
    import sys
    main()