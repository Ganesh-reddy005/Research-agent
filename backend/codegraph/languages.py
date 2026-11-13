"""Which grammar parses which file, and which syntax nodes are definitions in each language."""
from functools import lru_cache
from pathlib import PurePosixPath
import tree_sitter as ts

GRAMMARS = {  # suffix -> (grammar module, attribute holding its language)
    ".py": ("tree_sitter_python", "language"),
    ".c": ("tree_sitter_c", "language"), ".h": ("tree_sitter_cpp", "language"),  # headers are often C++
    ".cpp": ("tree_sitter_cpp", "language"), ".cc": ("tree_sitter_cpp", "language"),
    ".cxx": ("tree_sitter_cpp", "language"), ".hpp": ("tree_sitter_cpp", "language"),
    ".cu": ("tree_sitter_cpp", "language"),
    ".js": ("tree_sitter_javascript", "language"), ".jsx": ("tree_sitter_javascript", "language"),
    ".mjs": ("tree_sitter_javascript", "language"),
    ".ts": ("tree_sitter_typescript", "language_typescript"), ".tsx": ("tree_sitter_typescript", "language_tsx"),
    ".go": ("tree_sitter_go", "language"), ".rs": ("tree_sitter_rust", "language"),
    ".java": ("tree_sitter_java", "language"),
}

# Syntax node type -> kind of definition, across all supported languages
DEFINITIONS = {
    "function_definition": "function", "function_declaration": "function", "function_item": "function",
    "method_definition": "method", "method_declaration": "method", "constructor_declaration": "method",
    "class_definition": "class", "class_declaration": "class", "class_specifier": "class",
    "struct_specifier": "struct", "struct_item": "struct", "union_specifier": "struct",
    "enum_specifier": "enum", "enum_item": "enum", "enum_declaration": "enum",
    "interface_declaration": "interface", "trait_item": "interface",
    "type_definition": "type", "type_alias_declaration": "type", "type_spec": "type", "type_item": "type",
    "preproc_def": "macro", "preproc_function_def": "macro", "macro_definition": "macro",
    "mod_item": "module", "namespace_definition": "module",
}
# A struct/enum/class only counts as a definition when it has a body (not a mere use like `struct foo x;`)
NEEDS_BODY = {"struct_specifier", "union_specifier", "enum_specifier", "class_specifier"}
# Name-carrying nodes, for definitions whose name sits inside a declarator (C/C++)
NAME_NODES = {"identifier", "field_identifier", "type_identifier", "qualified_identifier",
              "destructor_name", "operator_name", "property_identifier"}
# Identifiers counted as references to a definition
REFERENCE_NODES = {"identifier", "field_identifier", "type_identifier", "property_identifier"}


def suffix(path: str) -> str:
    return PurePosixPath(path).suffix.lower()


def supported(path: str) -> bool:
    return suffix(path) in GRAMMARS


@lru_cache(maxsize=None)
def parser_for(file_suffix: str) -> ts.Parser | None:
    entry = GRAMMARS.get(file_suffix)
    if not entry:
        return None
    module_name, attribute = entry
    module = __import__(module_name)
    return ts.Parser(ts.Language(getattr(module, attribute)()))
