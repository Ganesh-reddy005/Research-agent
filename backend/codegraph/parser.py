"""Definitions and references in one source file.

Matching runs as tree-sitter queries (in C), so large repositories parse in seconds; Python only
looks at the matched nodes."""
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
import tree_sitter as ts
from codegraph.languages import DEFINITIONS, NAME_NODES, NEEDS_BODY, REFERENCE_NODES, parser_for, suffix

SIGNATURE_LINES = 4
SIGNATURE_CHARS = 200


@dataclass(frozen=True)
class Definition:
    name: str
    kind: str  # function, method, class, struct, enum, interface, type, macro, module
    path: str
    line: int  # 1-based, first line
    end_line: int
    signature: str
    parent: str = ""  # enclosing class, struct or namespace


@dataclass
class FileSymbols:
    path: str
    lines: int
    definitions: list[Definition] = field(default_factory=list)
    references: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))  # name -> lines


def _kinds_in(language: ts.Language, kinds) -> list[str]:
    return [k for k in kinds if language.id_for_node_kind(k, True)]


@lru_cache(maxsize=None)
def _queries(file_suffix: str) -> tuple[ts.Query, ts.Query] | None:
    parser = parser_for(file_suffix)
    if parser is None:
        return None
    language = parser.language
    definitions = " ".join(f"({k}) @def" for k in _kinds_in(language, DEFINITIONS))
    references = " ".join(f"({k}) @ref" for k in _kinds_in(language, REFERENCE_NODES))
    return ts.Query(language, definitions), ts.Query(language, references)


def _text(node: ts.Node) -> str:
    return node.text.decode("utf-8", "replace")


def _name_node(node: ts.Node) -> ts.Node | None:
    """The node holding a definition's name: its `name` field, or (C/C++) inside its declarators."""
    named = node.child_by_field_name("name")
    if named is not None:
        return named
    declarator = node.child_by_field_name("declarator")
    while declarator is not None:
        if declarator.type in NAME_NODES:
            return declarator
        inner = declarator.child_by_field_name("declarator")
        if inner is None:
            return next((c for c in declarator.named_children if c.type in NAME_NODES), None)
        declarator = inner
    return None


def _signature(node: ts.Node) -> str:
    """The definition's header: its first lines, up to where the body opens."""
    header = []
    for line in _text(node).splitlines()[:SIGNATURE_LINES]:
        header.append(line.strip())
        if line.rstrip().endswith((":", "{", ";")) or "{" in line:
            break
    return " ".join(header)[:SIGNATURE_CHARS]


def _parent(node: ts.Node) -> str:
    ancestor = node.parent
    while ancestor is not None:
        if ancestor.type in DEFINITIONS:
            name = _name_node(ancestor)
            if name is not None:
                return _text(name)
        ancestor = ancestor.parent
    return ""


def _definition(node: ts.Node, path: str) -> tuple[Definition, set[int]] | None:
    if node.type in NEEDS_BODY and node.child_by_field_name("body") is None:
        return None
    name_node = _name_node(node)
    if name_node is None:
        return None
    name, parent = _text(name_node), _parent(node)
    if "::" in name:  # C++ out-of-class definition: Foo::bar
        parent, name = name.rsplit("::", 1)
    kind = DEFINITIONS[node.type]
    if kind == "function" and parent:
        kind = "method"
    # Positions of the name and its parts (Foo::bar), so they don't count as references to themselves
    positions = {name_node.start_byte} | {c.start_byte for c in name_node.named_children}
    signature = _signature(node)
    if name not in signature:  # typedef struct { ... } name;  -- the name comes after the body
        signature = f"{signature} ... {name}"
    return Definition(name=name, kind=kind, path=path, line=node.start_point.row + 1,
                      end_line=node.end_point.row + 1, signature=signature, parent=parent), positions


def parse_file(path: str, source: bytes) -> FileSymbols | None:
    """Definitions and references in one file; None for languages without a grammar."""
    queries = _queries(suffix(path))
    if queries is None:
        return None
    tree = parser_for(suffix(path)).parse(source)
    symbols = FileSymbols(path=path, lines=source.count(b"\n") + 1)
    definition_query, reference_query = queries
    name_positions = set()
    for node in ts.QueryCursor(definition_query).captures(tree.root_node).get("def", []):
        found = _definition(node, path)
        if found:
            symbols.definitions.append(found[0])
            name_positions |= found[1]
    for node in ts.QueryCursor(reference_query).captures(tree.root_node).get("ref", []):
        if node.start_byte not in name_positions:
            symbols.references[_text(node)].append(node.start_point.row + 1)
    symbols.definitions.sort(key=lambda d: d.line)
    return symbols
