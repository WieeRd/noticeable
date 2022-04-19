import os
import pathlib

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union


@dataclass
class IgnoreRule:
    pattern: str
    regex: str
    negation: bool
    directory_only: bool
    anchored: bool
    base_path: Optional[pathlib.Path]
    source: Tuple[str, int]
    # I'm not gonna write down all the attributes, ok?
    __slots__ = __annotations__.keys()

    def __str__(self) -> str:
        # should I include the source?
        return f"{__class__.__name__}('{self.pattern}')"

    def match(self, path: str) -> bool:
        ...

    @classmethod
    def from_pattern(cls, pattern: str, source: str) -> Optional["IgnoreRule"]:
        """
        Parse a line of a .gitignore file and return `IgnoreRule`.

        Parameters
        ----------
        pattern: `str`
            A line of a .gitignore file.
        source: `str`
            Path to directory where the .gitignore file is located.
        """
        raise NotImplementedError


def is_ignored(path: str, rule_stack: List[List[IgnoreRule]]) -> bool:
    ignore = False
    for rules in rule_stack:
        for rule in rules:
            if rule.match(path):
                ignore = rule.negation
    return ignore


def _walk(path: str, ignore_fname: List[str], rule_stack: List[List[IgnoreRule]]):
    """
    Let the recursion begin!
    """
    root, dirs, files = next(os.walk(path))

    rules = []
    for fname in ignore_fname:
        if fname in files:
            with open(os.path.join(root, fname)) as ignore_file:
                for line in ignore_file:
                    if rule := IgnoreRule.from_pattern(line, root):
                        rules.append(rule)
    rule_stack.append(rules)

    files = [f for f in files if not is_ignored(f, rule_stack)]
    dirs = [d for d in dirs if not is_ignored(d, rule_stack)]

    yield root, files, dirs

    for d in dirs:
        yield from _walk(os.path.join(root, d), ignore_fname, rule_stack)

    rule_stack.pop()


def global_gitignore_rules() -> List[IgnoreRule]:
    # $GIT_DIR/info/exclude ($GIT_DIR = .git)
    # git config core.excludeFile
    raise NotImplementedError


def walk(path: str, ignore_fname: Union[str, List[str]] = ".gitignore"):
    """
    `os.walk()` but while following .gitignore rules.

    Parameters
    ----------
    path: `str`
        The path to start the walk from.

    ignore_fname: `str`, List[`str`]
        The name(s) of file(s) to read ignore rules from.

    Yields
    ------
    root: `str`
        Path to the directory that is currently being walked.
    dirnames: `List[str]`
        Names of subdirectories in `root` that aren't ignored.
    filenames: `List[str]`
        Names of files in `root` that aren't ignored.
    """
    # TODO: option to return ignored nodes instead

    if isinstance(ignore_fname, str):
        ignore_fname = [ignore_fname]

    git_dir = IgnoreRule.from_pattern(".git", path)
    assert isinstance(git_dir, IgnoreRule)

    global_rules = [git_dir]  # TODO: read global .gitignore files
    return _walk(path, ignore_fname, [global_rules])
