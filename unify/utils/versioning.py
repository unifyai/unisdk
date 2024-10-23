from typing import Any, Union, Optional, Dict

import unify


def get_code(fn: callable):
    """
    Takes a function and converts it to a string of the implementation within the file
    of the function (it doesn't parse the full AST, or sub-functions etc.)

    Args:
        fn: the function to convert to a string of the code implementation.

    Returns:
        The string of the code implementation.
    """
    with open(fn.__code__.co_filename) as file:
        offset_content = file.readlines()[fn.__code__.co_firstlineno - 1 :]
    first_line = offset_content[1]
    fn_indentation = len(first_line) - len(first_line.lstrip())
    fn_str = [offset_content[0], first_line]
    for line in offset_content[2:]:
        indentation = len(line) - len(line.lstrip())
        if indentation < fn_indentation:
            break
        fn_str.append(line)
    return "".join(fn_str)


class Versioned:

    def __init__(
        self,
        value: Any,
        version: Union[int, str] = 0,
        versions: Optional[Dict[Union[int, str], Any]] = None,
        name: Optional[str] = None,
    ):
        self._value = value
        self._version = version
        self._versions = {**(versions if versions else {}), **{version: value}}
        self._name = name

    def __repr__(self):
        return f"{self._value} [v:{self._version}]"

    def update(self, value: Any, version: Optional[Union[int, str]] = None):
        if version is None:
            previous_version = list(self._versions.keys())[-1]
            if isinstance(previous_version, int):
                version = previous_version + 1
            else:
                raise Exception(
                    "version must be specified explicitly if the"
                    "previous version is not of type int",
                )
        self._value = value
        self._version = version
        self._versions[version] = value

    def set_version(self, version: Union[int, str]):
        assert (
            version in self._versions
        ), "Cannot set to a version which is not present in the current versions."
        self._value = self._versions[version]
        self._version = version

    def at_version(self, version: Union[int, str]):
        return Versioned(self._versions[version], version, self._versions)

    def download(self, name: Optional[str] = None):
        if self._name is None:
            assert name is not None, (
                "If name is not set in the constructor, "
                "then name argument must be provided."
            )
            self._name = name
        self._versions = unify.get_versions(self._name)
        self._version, self._value = list(self._versions.items())[-1]

    @staticmethod
    def from_upstream(name: str):
        versions = unify.get_versions(name)
        version, value = list(versions.items())[-1]
        return Versioned(value=value, version=version, versions=versions, name=name)

    @property
    def value(self):
        return self._value

    @property
    def version(self):
        return self._version

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self._versions)


def versioned(value: Any, version: Union[int, str] = 0):
    """
    Thinly wrap input value into `unify.Versioned` class, such that it includes version
    information.

    Args:
        value: The value to wrap with attached version information.

        version: The version associated with this value.
        Defaults to 0.

    Returns:
        A `unify.Versioned` instance of the input value.
    """
    return Versioned(value, version)
