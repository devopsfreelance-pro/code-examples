def calculate(operation, a, b):
    if operation == "add":
        result = a + b
    else:
        if operation == "subtract":
            result = a - b
        else:
            if operation == "multiply":
                result = a * b
            else:
                if operation == "divide":
                    if b == 0:
                        result = 0
                    else:
                        result = a / b
                else:
                    result = None
    return result
