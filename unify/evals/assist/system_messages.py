# Implement #
# ----------#

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
You should write a Python implementation for a function `{name}` with the
following signature, docstring and example inputs:

def {name}{signature}
    \"\"\"
{docstring}
    \"\"\"

{name}({args} {kwargs})

    """
UPDATING_CODING_SYS_MESSAGE = """
You should *update* the Python implementation (preserving the function name,
arguments, and general structure), and only make changes as requested by the user
in the chat. The following example inputs should be compatible with the implementation:

{name}({args} {kwargs})

"""

DOCSTRING_SYS_MESSAGE_HEAD = """
We need to implement a new function `{name}`, but before we implement it we first
need to  decide on exactly how it should behave.
"""

DOCSTRING_SYS_MESSAGE_FIRST_CONTEXT = """
To help us, we know that the function `{child_name}` is called inside the function
`{parent_name}`, which has the following implementation:

```python
{parent_implementation}
```

Specifically, the line where `{child_name}` is called is: `{calling_line}`.
"""

DOCSTRING_SYS_MESSAGE_EXTRA_CONTEXT = """
This function (`{child_name}`) is itself called inside another function `{parent_name}`,
which has the following implementation:

```python
{parent_implementation}
```

Specifically, the line where `{child_name}` is called is: `{calling_line}`.
"""

DOCSTRING_SYS_MESSAGE_TAIL = """
Given all of this context, your task is to provide a well informed proposal for the
docstring and argument specification (with typing) for the new function `{name}`,
with an empty implementation `pass`, in the following format:

```python
def {name}({arg1}: {type1}, {arg2}: {type2} = {default2}, ...):
    \"\"\"
    {A very thorough description for exactly what this function needs to do.}

    Args:
        {arg1}: {arg1 description}

        {arg2}: {arg2 description}

    Returns:
        {return description}
    \"\"\"
    pass
```

Please respond in the format as above, and write nothing else after your answer.
"""

# Suggest #
# --------#

SUGGEST_SYS_MESSAGE = """

Your task is to propose changes to one parameter in the experiment configuration
in order to try and {relation} the metric `{metric}`. You should pay attention to all of
the log data, and pay special attention to examples where `{metric}` has a {low|high}
value. Try to work out why this might be, based on the full context of the experiment
configuration. You should then choose the experiment configuration parameter you'd like
to change (if there is more than one), and suggest a sensible new value to try.

The experiment configuration parameters that can be changed are as follows:

{configs}

The full set of evaluation logs for different combinations of these experiment
configuration parameters are as follows:

{evals}

You should think through this process step by step, and explain which parameter you've
chosen and why you think this parameter is contributing to the poor performing examples.

You should then propose a new value for this parameter, and why you believe this new
value will help. The parameter can be of any type. It might be a `str` system prompt,
a piece of Python code, a single numeric value, or dictionary, or any other type.

At the very end of your response, please respond as follows, filling in the placeholders
{parameter_name} and {parameter_value}:

"parameter":
"{parameter_name}"

"value":
{parameter_value}

"""
