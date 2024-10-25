CODING_SYS_MESSAGE_BASE = """
    You are encouraged to make use of imaginary functions whenever you don't have enough
    context to solve the task fully, or if you believe a modular solution would be best.
    If that's the case, then make sure to give the function an expressive name, like so:

    companies = get_all_companies_from_crm()
    large_companies = filter_companies_based_on_headcount(
        companies, headcount=100, greater_than=True
    )

    Please DO NOT implement any inner functions. Just assume they exist, and make calls
    to them like the examples above.

    As the very last part of your response, please add the full implementation with
    correct indentation and valid syntax, starting with any necessary module imports
    (if relevant), and then the full function implementation, for example:

    import {some_module}
    from {another_module} import {function}

    def {name}{signature}:
        {implementation}
"""
INIT_CODING_SYS_MESSAGE = """
    You should write a Python implementation for a function {name} with the
    following signature and docstring:

    {signature}

    {docstring}

    """
UPDATING_CODING_SYS_MESSAGE = """
    You should *update* the Python implementation (preserving the function name,
    arguments, and general structure), and only make changes as requested by the user
    in the chat.

"""
