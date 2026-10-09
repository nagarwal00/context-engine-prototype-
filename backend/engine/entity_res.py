"""
Entity Resolution Engine (Section 7.1)
Normalizes files/modules, parses Python AST to identify functions/methods,
and tracks dependency manifests across commits.
"""
import ast
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from backend.models import Entity
from backend.db import Database

class EntityResolver:
    def __init__(self, db: Database):
        self.db = db

    def normalize_path(self, path: str) -> str:
        """Normalizes file path across OS platforms."""
        clean = path.replace("\\", "/").strip()
        while clean.startswith("./"):
            clean = clean[2:]
        return clean

    def resolve_file_entity(self, repo: str, file_path: Optional[str] = None, summary: Optional[str] = None, canonical_path: Optional[str] = None) -> Entity:
        actual_path = file_path or canonical_path or "unknown_file"
        norm_path = self.normalize_path(actual_path)
        entity_id = f"ent_file_{repo.replace('/', '_')}_{norm_path.replace('/', '_').replace('.', '_')}"
        
        entity = Entity(
            entity_id=entity_id,
            entity_type="file",
            canonical_path=norm_path,
            aliases=[actual_path, os.path.basename(actual_path)],
            repo=repo,
            current_state_summary=summary or f"Source file {norm_path}"
        )
        self.db.upsert_entity(entity)
        return entity

    def extract_functions_from_python_code(self, code_str: str) -> List[Tuple[str, int, int]]:
        """
        Uses Python AST to extract all top-level functions and class methods.
        Returns list of (function_name, start_line, end_line)
        """
        results = []
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    results.append((node.name, node.lineno, getattr(node, "end_lineno", node.lineno)))
        except Exception:
            # Fallback regex if syntax error
            for m in re.finditer(r"def\s+([a-zA-Z0-9_]+)\s*\(", code_str):
                results.append((m.group(1), 1, 1))
        return results

    def parse_python_ast_functions(self, code_str: str, file_path: str = "") -> List[Dict[str, Any]]:
        """
        Parses Python code AST to return list of dicts with function names and line numbers.
        """
        results = []
        raw_fns = self.extract_functions_from_python_code(code_str)
        for name, start, end in raw_fns:
            results.append({"name": name, "lineno": start, "end_lineno": end})
        return results

    def resolve_function_entity(
        self,
        repo: str,
        file_path: Optional[str] = None,
        function_name: str = "",
        summary: Optional[str] = None,
        canonical_path: Optional[str] = None
    ) -> Entity:
        actual_path = file_path or canonical_path or "unknown_file"
        norm_path = self.normalize_path(actual_path)
        canonical = f"{norm_path}::{function_name}"
        entity_id = f"ent_fn_{repo.replace('/', '_')}_{canonical.replace('/', '_').replace('::', '_').replace('.', '_')}"

        entity = Entity(
            entity_id=entity_id,
            entity_type="function",
            canonical_path=canonical,
            aliases=[f"{os.path.basename(actual_path)}::{function_name}", function_name],
            repo=repo,
            current_state_summary=summary or f"Function {function_name} in {norm_path}"
        )
        self.db.upsert_entity(entity)
        return entity

    def parse_dependency_manifest(self, manifest_content: str, filename: str = "requirements.txt") -> Dict[str, str]:
        """Parses dependency specifications, e.g. redis==4.5.1"""
        deps = {}
        for line in manifest_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([=><~!].+)?$", line)
            if match:
                pkg = match.group(1).lower()
                ver = match.group(2).strip() if match.group(2) else "latest"
                deps[pkg] = ver
        return deps

    def resolve_dependency_entity(self, repo: str, pkg_name: str, version_spec: str) -> Entity:
        canonical = f"deps::{pkg_name}"
        entity_id = f"ent_dep_{repo.replace('/', '_')}_{pkg_name}"

        entity = Entity(
            entity_id=entity_id,
            entity_type="dependency",
            canonical_path=canonical,
            aliases=[f"{pkg_name} {version_spec}", pkg_name],
            repo=repo,
            current_state_summary=f"Dependency package {pkg_name} ({version_spec})"
        )
        self.db.upsert_entity(entity)
        return entity
