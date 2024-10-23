import inspect
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
    return inspect.getsource(fn)


class Versioned:

    def __init__(
        self,
        value: Any,
        version: Union[int, str] = 0,
        versions: Optional[Dict[Union[int, str], Any]] = None,
        name: Optional[str] = None,
    ):
        if isinstance(value, unify.Dataset):
            assert value.name is not None, "Versioned datasets must have a name"
            value.set_name(f"{value.name}/{version}")
        elif isinstance(value, Versioned):
            value = value.value
        self._value = value
        self._version = version
        self._versions = {
            **(versions if versions else {}),
            **{version: value},
        }
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

    def set_latest(self):
        self.set_version(list(self._versions.keys())[-1])

    def set_name(self, name: str):
        self._name = name

    def at_version(self, version: Union[int, str]):
        return Versioned(self._versions[version], version, self._versions)

    def add_version(self, version: Union[int, str], value: Any):
        self._versions[version] = value

    def download(self, name: Optional[str] = None):
        if self._name is None:
            assert name is not None, (
                "If name is not set in the constructor, "
                "then name argument must be provided."
            )
            self._name = name
        self._versions = unify.get_versions(self._name)
        self._version, self._value = list(self._versions.items())[-1]

    def sync(self, name: Optional[str] = None):
        if self._name is None:
            assert name is not None, (
                "If name is not set in the constructor, "
                "then name argument must be provided."
            )
            self._name = name
        logs = unify.get_logs_with_fields(self._name)
        logs_to_version = list()
        for log in logs:
            if self._name not in log.entries:
                # already versioned upstream
                continue
            upstream_val = log.entries[self._name]
            for local_version, local_val in self._versions.items():
                if upstream_val != local_val:
                    continue
                logs_to_version.append((log, local_version))
                break
        unify.map(lambda l, v: l.version_entries(**{self._name: v}), logs_to_version)
        self.download()

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
    def versions(self):
        return self._versions

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self._versions)

    def __contains__(self, version: Union[int, str]):
        return version in self._versions


def versioned(
    value: Any,
    version: Union[int, str] = 0,
    versions: Optional[Dict[Union[int, str], Any]] = None,
    name: Optional[str] = None,
) -> Versioned:
    """
    Thinly wrap input value into `unify.Versioned` class, such that it includes version
    information.

    Args:
        value: The value to wrap with attached version information.

        version: The version associated with this value.
        Defaults to 0.

        versions: Dictionary of versions to store in the instance

        name: The name of the entry being versioned.

    Returns:
        A `unify.Versioned` instance of the input value.
    """
    return Versioned(value=value, version=version, versions=versions, name=name)
