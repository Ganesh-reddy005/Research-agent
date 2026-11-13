"""The code graph: definitions, references and file ranking, on small made-up repositories."""
from codegraph.graph import CodeGraph, specificity, words
from codegraph.parser import parse_file
from codegraph.repomap import repo_map

def write(root, files):
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)

def test_python_definitions_know_their_class_and_references_skip_their_own_names():
    symbols = parse_file("m.py", b"class Model:\n    def forward(self, x):\n        return helper(x)\n\ndef helper(x):\n    return Model()\n")
    assert [(d.kind, d.name, d.parent, d.line) for d in symbols.definitions] == [
        ("class", "Model", "", 1), ("method", "forward", "Model", 2), ("function", "helper", "", 5)]
    assert symbols.references["helper"] == [3] and symbols.references["Model"] == [6]
    assert "forward" not in symbols.references

def test_c_and_cpp_definitions_include_macros_typedefs_and_out_of_class_methods():
    source = (b"#define BLOCK 32\ntypedef struct { float d; } block_t;\nstruct use_only x;\n"
              b"static void quantize(const float * x) { dot(x); }\nvoid Engine::run(int n) { quantize(0); }\n")
    found = {(d.kind, d.name, d.parent) for d in parse_file("q.cpp", source).definitions}
    assert found == {("macro", "BLOCK", ""), ("type", "block_t", ""), ("function", "quantize", ""), ("method", "run", "Engine")}
    multiline = parse_file("q.h", b"typedef struct {\n    float d;\n    char qs[16];\n} block_q4;\n").definitions[0]
    assert multiline.signature == "typedef struct { ... block_q4"  # the name follows the body, so it's appended

def test_unsupported_files_are_skipped():
    assert parse_file("notes.md", b"# hi") is None

def test_lookups_and_ranking_follow_who_depends_on_whom(tmp_path):
    write(tmp_path, {
        "core/tensor.py": "class TensorStore:\n    pass\n\ndef make_tensor():\n    return TensorStore()\n",
        "a.py": "from core.tensor import make_tensor\nmake_tensor()\n",
        "b.py": "from core.tensor import make_tensor, TensorStore\nmake_tensor(); TensorStore()\n",
        "tests/test_tensor.py": "def test_it():\n    make_tensor(); make_tensor()\n",
        "vendors/lib.js": "function huge() {}\n",
        ".hidden/x.py": "def secret(): pass\n",
    })
    graph = CodeGraph.build(tmp_path)
    assert "vendors/lib.js" not in graph.files and ".hidden/x.py" not in graph.files
    assert [(d.path, d.line) for d in graph.find_definition("make_tensor")] == [("core/tensor.py", 4)]
    assert ("a.py", 2) in graph.find_references("make_tensor")
    ranked = [p for p, _ in graph.ranked_files()]
    assert ranked[0] == "core/tensor.py"  # everything depends on it
    assert ranked[-1] == "tests/test_tensor.py"  # tests rank below the code they test
    assert [p for p, _ in graph.ranked_files(focus=["b"])][0] != "b.py"  # too short to be a focus word
    assert set(graph.similar_names("tensor")) == {"make_tensor", "TensorStore"}

def test_focus_puts_matching_files_first(tmp_path):
    write(tmp_path, {"core.py": "def shared_helper(): pass\n",
                     "quant.py": "from core import shared_helper\ndef quantize_rows(): shared_helper()\n",
                     "other.py": "from core import shared_helper\ndef render_page(): shared_helper()\n"})
    graph = CodeGraph.build(tmp_path)
    assert [p for p, _ in graph.ranked_files(focus=["quantize"])][0] == "quant.py"
    assert [p for p, _ in graph.ranked_files(focus=["render"])][0] == "other.py"

def test_generic_names_count_less_than_specific_ones():
    assert words("quantizeRow_q4") == {"quantize", "row", "q", "4"}
    assert specificity("url") < specificity("parse_github_url") == specificity("RepoRef") == 1.0

def test_test_fakes_do_not_attract_references_from_real_code(tmp_path):
    # Real code calls response.json(); the only `json` defined is a fake in a test
    write(tmp_path, {"client.py": "def fetch_page():\n    return response.json()\n",
                     "api.py": "from client import fetch_page\nfetch_page()\n",
                     "tests/test_client.py": "class Fake:\n    def json(self): return {}\nfetch_page()\n"})
    assert "tests/test_client.py" not in CodeGraph.build(tmp_path)._edges().get("client.py", {})

def test_repo_map_stays_within_budget_and_points_to_the_rest(tmp_path):
    write(tmp_path, {f"m{i}.py": "".join(f"def function_number_{i}_{j}(argument): pass\n" for j in range(10))
                     for i in range(30)})
    text = repo_map(CodeGraph.build(tmp_path), budget_tokens=100)
    assert len(text) < 100 * 4 + 200
    assert "more files (use outline, find_definition or grep)" in text
