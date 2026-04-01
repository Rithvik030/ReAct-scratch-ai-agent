def calculate(expression):

    try:
        result = eval(expression)
        return str(result)

    except Exception:
        return "Invalid mathematical expression."