from tree_sitter import Language, Parser, Query
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript

from tig.services.tree_sitter.queries import (
    py_query,
    js_query,
    ts_query,
    tsx_query,
)


def get_parser(ext: str) -> tuple[Parser, Query]:
    if ext == "py":
        PY_LANG = Language(tspython.language())
        parser = Parser(PY_LANG)
        query = PY_LANG.query(py_query)
        return parser, query
    if ext == "js" or ext == "jsx":
        LANG = Language(tsjavascript.language())
        parser = Parser(LANG)
        query = LANG.query(js_query)
        return parser, query
    if ext == "ts":
        LANG = Language(tstypescript.language_typescript())
        parser = Parser(LANG)
        query = LANG.query(ts_query)
        return parser, query
    if ext == "tsx":
        LANG = Language(tstypescript.language_tsx())
        parser = Parser(LANG)
        query = LANG.query(tsx_query)
        return parser, query
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
