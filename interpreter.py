class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value



def evaluate(node, variables):
    if node.kind == "literal":
        return node.value

    if node.kind == "variable":
        if node.value not in variables:
            raise RuntimeError(f"Undefined variable: {node.value}")
        return variables[node.value]

    if node.kind == "unary":
        operator, operand = node.value

        if operator == "zot":
            return not evaluate(operand, variables)

        raise RuntimeError(f"Unknown unary operator: {operator}")

    if node.kind == "binary":
        operator, left, right = node.value

        if operator == "zand":
            return evaluate(left, variables) and evaluate(right, variables)

        if operator == "zor":
            return evaluate(left, variables) or evaluate(right, variables)

        a = evaluate(left, variables)
        b = evaluate(right, variables)

        if operator == "+": return a + b
        if operator == "-": return a - b
        if operator == "*": return a * b
        if operator == "/": return a / b
        if operator == "%": return a % b
        if operator == "==": return a == b
        if operator == "!=": return a != b
        if operator == ">": return a > b
        if operator == "<": return a < b
        if operator == ">=": return a >= b
        if operator == "<=": return a <= b

        raise RuntimeError(f"Unknown binary operator: {operator}")

    if node.kind == "list":
        return [evaluate(element, variables) for element in node.children]

    if node.kind == "index":
        collection_node, index_node = node.value
        collection = evaluate(collection_node, variables)
        index = evaluate(index_node, variables)

        if not isinstance(collection, list):
            raise RuntimeError("Indexing requires a list")

        if type(index) is not int:
            raise RuntimeError("List indices must be integers")

        try:
            return collection[index]
        except IndexError:
            raise RuntimeError(f"List index out of range: {index}")

    if node.kind == "call":
        name, arguments = node.value
        values = [evaluate(arg, variables) for arg in arguments]

        if name == "zange":
            if not 1 <= len(values) <= 3:
                raise RuntimeError("zange() accepts 1 to 3 arguments")

            if not all(type(value) is int for value in values):
                raise RuntimeError("zange() arguments must be integers")

            return range(*values)

        if name not in variables:
            raise RuntimeError(f"Undefined function: {name}")

        function = variables[name]

        if not (isinstance(function, tuple) and len(function) == 3
                and function[0] == "__zy_function__"):
            raise RuntimeError(f"{name} is not a function")

        _, parameters, body = function

        if len(values) != len(parameters):
            raise RuntimeError(
                f"{name}() expects {len(parameters)} arguments, "
                f"got {len(values)}"
            )

        local_variables = dict(variables)
        local_variables.update(zip(parameters, values))

        try:
            execute(body, local_variables)
        except ReturnSignal as result:
            return result.value

        return None
        
    if node.kind == "method_call":
        object_node, method, arguments = node.value
        obj = evaluate(object_node, variables)
        values = [evaluate(arg, variables) for arg in arguments]

        if not isinstance(obj, list):
            raise RuntimeError("List methods require a list")

        if method == "zappend":
            if len(values) != 1:
                raise RuntimeError("zappend() requires exactly 1 argument")
            obj.append(values[0])
            return None

        if method == "zpop":
            if len(values) != 0:
                raise RuntimeError("zpop() takes no arguments")
            if not obj:
                raise RuntimeError("Cannot zpop() an empty list")
            return obj.pop()

        if method == "zlength":
            if len(values) != 0:
                raise RuntimeError("zlength() takes no arguments")
            return len(obj)

        raise RuntimeError(f"Unknown list method: {method}")

    raise RuntimeError(f"Cannot evaluate: {node.kind}")


def execute(statements, variables=None):
    if variables is None:
        variables = {}

    for node in statements:
        if node.kind == "assign":
            name, expression = node.value
            variables[name] = evaluate(expression, variables)
        elif node.kind == "index_assign":
            name, index_node, expression = node.value

            if name not in variables:
                raise RuntimeError(f"Undefined variable: {name}")

            collection = variables[name]
            index = evaluate(index_node, variables)
            value = evaluate(expression, variables)

            if not isinstance(collection, list):
                raise RuntimeError("Index assignment requires a list")

            if type(index) is not int:
                raise RuntimeError("List indices must be integers")

            try:
                collection[index] = value
            except IndexError:
                raise RuntimeError(f"List index out of range: {index}")
            
        elif node.kind == "print":
            print(evaluate(node.value, variables))

        elif node.kind == "if":
            condition = evaluate(node.value, variables)

            try:
                if condition:
                    execute(node.children, variables)
                else:
                    execute(node.otherwise, variables)
            except (BreakSignal, ContinueSignal):
                raise

        elif node.kind == "while":
            while evaluate(node.value, variables):
                execute(node.children, variables)

        elif node.kind == "for":
            variable, arguments = node.value
            values = [evaluate(arg, variables) for arg in arguments]

            if not 1 <= len(values) <= 3:
                raise RuntimeError("zange() accepts 1 to 3 arguments")

            if not all(type(value) is int for value in values):
                raise RuntimeError("zange() arguments must be integers")

            for value in range(*values):
                variables[variable] = value

                try:
                    execute(node.children, variables)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break

        elif node.kind == "function":
            name, parameters = node.value
            variables[name] = (
                "__zy_function__", parameters, node.children
            )

        elif node.kind == "return":
            raise ReturnSignal(evaluate(node.value, variables))
        elif node.kind == "break":
            raise BreakSignal()

        elif node.kind == "continue":
            raise ContinueSignal()
        elif node.kind == "expression":
            evaluate(node.value, variables)
        else:
            raise RuntimeError(f"Unknown statement: {node.kind}")
