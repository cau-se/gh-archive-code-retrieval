"""A custom tokenizer for Java files."""
import javalang


class JavaPreTokenizer:

    @staticmethod
    def java_tokenize(i, normalized_string):
        values = []
        try:
            for elem in javalang.tokenizer.tokenize(normalized_string.normalized):
                start = elem.position.column - 1
                stop = start + len(elem.value)
                values.append(normalized_string[start:stop])
        except:
            values = []
        return values

    def pre_tokenize(self, pretok):
        pretok.split(self.java_tokenize)
