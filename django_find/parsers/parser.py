
class Parser(object):
    """
    The base class for all parsers.
    """

    def __init__(self, token_list):
        self.token_list = token_list
        self._reset()

    def _reset(self):
        self.offset = 0
        self.line = 0
        self.error = ''

    def _get_next_token(self):
        if len(self.input) <= self.offset:
            return 'EOF', None

        # Walk through the list of tokens, trying to find a match.
        for token_name, token_regex in self.token_list:
            match = token_regex.match(self.input, self.offset)
            if not match:
                continue

            string = match.group(0)
            self.offset += len(string)
            self.line += string.count('\n')
            return token_name, match

        # Ending up here no matching token was found.
        return None, None
