
from dataclasses import dataclass


@dataclass
class Node:
    kind: str
    value: object = None
    children: list = None
    otherwise: list = None


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def match(self, kind, value=None):
        token = self.current()
        if token[0] == kind and (value is None or token[1] == value):
            self.advance()
            return True
        return False

    def expect(self, kind, value=None):
        if not self.match(kind, value):
            raise SyntaxError(f"Expected {value or kind}, got {self.current()}")

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

    def parse(self):
        statements = self.parse_block()
        self.expect("EOF")
        return statements

    def parse_block(self):
        statements = []
        self.skip_newlines()

        while self.current()[0] not in ("DEDENT", "EOF"):
            statements.append(self.parse_statement())
            self.skip_newlines()

        return statements

    
    def parse_statement(self):
        token = self.current()

        if token[0] == "KEYWORD" and token[1] == "zprint":
            self.advance()
            self.expect("OPERATOR", "(")
            expression = self.parse_expression()
            self.expect("OPERATOR", ")")
            self.expect("NEWLINE")
            return Node("print", expression)

        if token[0] == "KEYWORD" and token[1] == "zif":
            return self.parse_if()

        if token[0] == "KEYWORD" and token[1] == "zhile":
            return self.parse_while()

        if token[0] == "KEYWORD" and token[1] == "zfor":
            return self.parse_for()

        if token[0] == "KEYWORD" and token[1] == "zef":
            return self.parse_function()

        if token[0] == "KEYWORD" and token[1] == "zeturn":
            self.advance()
            expression = self.parse_expression()
            self.expect("NEWLINE")
            return Node("return", expression)

        if token[0] == "KEYWORD" and token[1] == "zreak":
            self.advance()
            self.expect("NEWLINE")
            return Node("break")

        if token[0] == "KEYWORD" and token[1] == "zontinue":
            self.advance()
            self.expect("NEWLINE")
            return Node("continue")

        
        
        
        if token[0] == "IDENTIFIER":
            name = self.advance()[1]

            if self.match("OPERATOR", "="):
                expression = self.parse_expression()
                self.expect("NEWLINE")
                return Node("assign", (name, expression))

            if self.match("OPERATOR", "["):
                index = self.parse_expression()
                self.expect("OPERATOR", "]")
                self.expect("OPERATOR", "=")
                expression = self.parse_expression()
                self.expect("NEWLINE")
                return Node("index_assign", (name, index, expression))

            if self.match("OPERATOR", "."):
                method = self.advance()

                if method[0] != "IDENTIFIER":
                    raise SyntaxError("Expected a list method name")

                self.expect("OPERATOR", "(")
                arguments = []

                if not self.match("OPERATOR", ")"):
                    while True:
                        arguments.append(self.parse_expression())

                        if self.match("OPERATOR", ")"):
                            break

                        self.expect("OPERATOR", ",")

                self.expect("NEWLINE")
                return Node(
                    "expression",
                    Node("method_call", (Node("variable", name),
                                         method[1], arguments))
                )

        raise SyntaxError(f"Expected assignment or method call after '{name}'")



    def parse_if(self):
        self.expect("KEYWORD", "zif")
        condition = self.parse_expression()
        self.expect("OPERATOR", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        body = self.parse_block()
        self.expect("DEDENT")

        otherwise = []
        if self.current()[0] == "KEYWORD" and self.current()[1] == "zlse":
            self.advance()
            self.expect("OPERATOR", ":")
            self.expect("NEWLINE")
            self.expect("INDENT")
            otherwise = self.parse_block()
            self.expect("DEDENT")

        return Node("if", condition, body, otherwise)

    def parse_function(self):
        self.expect("KEYWORD", "zef")

        if self.current()[0] != "IDENTIFIER":
            raise SyntaxError("Expected a function name")

        name = self.advance()[1]
        self.expect("OPERATOR", "(")

        parameters = []

        if not self.match("OPERATOR", ")"):
            while True:
                if self.current()[0] != "IDENTIFIER":
                    raise SyntaxError("Expected a parameter name")

                parameters.append(self.advance()[1])

                if self.match("OPERATOR", ")"):
                    break

                self.expect("OPERATOR", ",")

        self.expect("OPERATOR", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")

        body = self.parse_block()
        self.expect("DEDENT")

        return Node("function", (name, parameters), body)

    def parse_comparison(self):
        left = self.parse_addition()

        if self.current()[0] == "OPERATOR" and self.current()[1] in (
            "==", "!=", ">", "<", ">=", "<="
        ):
            operator = self.advance()[1]
            right = self.parse_addition()
            return Node("binary", (operator, left, right))

        return left


    def parse_addition(self):
        left = self.parse_multiplication()

        while self.current()[0] == "OPERATOR" and self.current()[1] in ("+", "-"):
            operator = self.advance()[1]
            right = self.parse_multiplication()
            left = Node("binary", (operator, left, right))

        return left

    def parse_multiplication(self):
        left = self.parse_atom()

        while self.current()[0] == "OPERATOR" and self.current()[1] in ("*", "/", "%"):
            operator = self.advance()[1]
            right = self.parse_atom()
            left = Node("binary", (operator, left, right))

        return left

    
    
    def parse_atom(self):
        token = self.current()

        if token[0] == "NUMBER":
            self.advance()
            value = float(token[1]) if "." in token[1] else int(token[1])
            node = Node("literal", value)

        elif token[0] == "STRING":
            self.advance()
            node = Node("literal", token[1])

        elif token[0] == "KEYWORD" and token[1] in ("zrue", "zalse"):
            self.advance()
            node = Node("literal", token[1] == "zrue")

        elif token[0] == "IDENTIFIER":
            self.advance()

            if self.match("OPERATOR", "("):
                arguments = []

                if not self.match("OPERATOR", ")"):
                    while True:
                        arguments.append(self.parse_expression())

                        if self.match("OPERATOR", ")"):
                            break

                        self.expect("OPERATOR", ",")

                node = Node("call", (token[1], arguments))
            else:
                node = Node("variable", token[1])

        elif self.match("OPERATOR", "("):
            node = self.parse_expression()
            self.expect("OPERATOR", ")")

        elif self.match("OPERATOR", "["):
            elements = []

            if not self.match("OPERATOR", "]"):
                while True:
                    elements.append(self.parse_expression())

                    if self.match("OPERATOR", "]"):
                        break

                    self.expect("OPERATOR", ",")

            node = Node("list", children=elements)

        else:
            raise SyntaxError(f"Unexpected expression token {token}")

        while True:
            if self.match("OPERATOR", "["):
                index = self.parse_expression()
                self.expect("OPERATOR", "]")
                node = Node("index", (node, index))

            elif self.match("OPERATOR", "."):
                method = self.advance()

                if method[0] != "IDENTIFIER":
                    raise SyntaxError("Expected a method name")

                self.expect("OPERATOR", "(")
                arguments = []

                if not self.match("OPERATOR", ")"):
                    while True:
                        arguments.append(self.parse_expression())

                        if self.match("OPERATOR", ")"):
                            break

                        self.expect("OPERATOR", ",")

                node = Node("method_call", (node, method[1], arguments))

            else:
                break

        return node


    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()

        while self.match("KEYWORD", "zor"):
            right = self.parse_and()
            left = Node("binary", ("zor", left, right))

        return left

    def parse_and(self):
        left = self.parse_not()

        while self.match("KEYWORD", "zand"):
            right = self.parse_not()
            left = Node("binary", ("zand", left, right))

        return left

    def parse_not(self):
        if self.match("KEYWORD", "zot"):
            return Node("unary", ("zot", self.parse_not()))
        return self.parse_comparison()
    
    def parse_while(self):
        self.expect("KEYWORD", "zhile")
        condition = self.parse_expression()
        self.expect("OPERATOR", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")

        body = self.parse_block()
        self.expect("DEDENT")

        return Node("while", condition, body)

    def parse_for(self):
        self.expect("KEYWORD", "zfor")

        if self.current()[0] != "IDENTIFIER":
            raise SyntaxError("Expected a loop variable after zfor")

        variable = self.advance()[1]
        self.expect("KEYWORD", "zin")
        self.expect("IDENTIFIER", "zange")
        self.expect("OPERATOR", "(")

        arguments = [self.parse_expression()]

        if self.match("OPERATOR", ","):
            arguments.append(self.parse_expression())

            if self.match("OPERATOR", ","):
                arguments.append(self.parse_expression())

        self.expect("OPERATOR", ")")
        self.expect("OPERATOR", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")

        body = self.parse_block()
        self.expect("DEDENT")

        return Node("for", (variable, arguments), body)
