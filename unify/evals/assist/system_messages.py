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

# Update #
# -------#

SUGGEST_SYS_MESSAGE = """

Your task is to propose new changes to one parameter in the experiment configuration
in order to try and {relation} the metric `{metric}`. Your task is to try and beat the
highest performing experiment, based on the historical experiments presented. Don't pay
attention to improving the poorest performing experiments, your task is to improve upon
the highest performing, using all of the historical context to make sense of all the
failure modes observed thus far across all experiments. The highest performing
experiment (shown last) presents *all* of the log data, whereas all other experiments
only present the logs which are *different* to the highest performing. Therefore, if a
log is missing, then this means the result was the *same* as the highest performing.

You should not *cheat* to improve the `{metric}`. For example, making the questions in
the test set much easier is not a good proposal. Neither is hacking the evaluator
function to always return a high score. However, fixing issues in how the questions are
formatted or how the data is presented in the test dataset *might* be a valid
improvement, as might making the evaluator code more robust. The overall intention is to
improve the genuine performance and capability of the system, with `{metric}` being a
good proxy for this, provided that we are striving to {relation} the metric `{metric}`
*in good faith* (without *shortcuts* or *cheating*).

You should pay attention to the highest performing experiments, and pay special
attention to examples in these experiments where `{metric}` has a {low|high} value.
Lower performing experiments might provide some additional helpful context, but likely
will not be as useful as the highest performing experiments, given that we're trying to
further improve upon the *best* experiment so far.

Try to work out why some examples are still failing. You should then choose the
parameter you'd like to change (if there is more than one), and suggest a sensible new
value to try for the next experiment, in an attempt to beat all prior results.

The parameters that can be changed are as follows:

{configs}

The full set of evaluation logs for different experiments, ordered from the lowest
performing to highest performing, are as follows:

{evals}

You should think through this process step by step, and explain which parameter you've
chosen and why you think this parameter is contributing to the poor performing logs
in the highest performing experiment.

You should then propose a new value for this parameter, and why you believe this new
value will help to improve things further. The parameter can be of any type. It might be
a `str` system prompt, a piece of Python code, a single numeric value, or dictionary,
or any other type.

At the very end of your response, please respond as follows, filling in the placeholders
{parameter_name} and {parameter_value}:

parameter:
"{parameter_name}"

value:
{parameter_value}

"""
