#!/usr/bin/env python3
"""Analise generica mestre-filho: controllers, sub-rotas e agregado (leitura do repo)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Sufixos que indicam controller dedicado ao filho (prefixo = stem do pai).
CHILD_CONTROLLER_SUFFIXES: tuple[str, ...] = (
    "ClientesSuperiores",
    "ClienteSuperior",
    "Dependente",
    "Dependentes",
    "Filho",
    "Filha",
    "Superior",
    "Superiores",
    "Subordinado",
    "Pagamento",
    "Pagamentos",
    "Recebimento",
    "Recebimentos",
    "Item",
    "Itens",
    "Aditivo",
    "Aditivos",
    "Contato",
    "Contatos",
    "Endereco",
    "Enderecos",
    "Cnae",
    "Cnaes",
    "Destinatario",
    "Destinatarios",
    "Subcategoria",
    "Subcategorias",
    "DadosBancarios",
)

MAPPING_ANNOTATION = re.compile(
    r"@(?P<kind>Get|Post|Put|Patch|Delete)Mapping\s*\("
    r"(?:\s*value\s*=\s*)?"
    r"(?:\{\s*)?[\"']([^\"']+)[\"']",
    re.MULTILINE,
)
CLASS_RE = re.compile(r"public\s+class\s+(\w+Controller)\b")
REQUEST_MAPPING_RE = re.compile(
    r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)[\"']",
)
ID_SEGMENT_RE = re.compile(r"\{id[a-zA-Z]*\}")


@dataclass(frozen=True)
class ControllerInfo:
    class_name: str
    path: Path
    rel_path: str
    base_mapping: str
    http_paths: tuple[str, ...]
    nested_under_id: tuple[str, ...]


@dataclass(frozen=True)
class DedicatedChildPair:
    parent_class: str
    child_class: str
    parent_rel: str
    child_rel: str
    child_suffix: str
    parent_nested_paths: tuple[str, ...]


@dataclass
class FilhoPaiAnalysis:
    dedicated_children: list[DedicatedChildPair] = field(default_factory=list)
    aggregate_notes: list[str] = field(default_factory=list)

    def child_rel_paths(self) -> list[str]:
        return [p.child_rel for p in self.dedicated_children]

    def has_findings(self) -> bool:
        return bool(self.dedicated_children or self.aggregate_notes)


def default_allowlist() -> set[str]:
    extra = os.environ.get("CURSOR_VALIDATOR_CHILD_CONTROLLER_ALLOWLIST", "").strip()
    names = {"ContaReceberRecebimentoController.java"}
    if extra:
        for part in extra.split(","):
            p = part.strip()
            if p:
                names.add(p if p.endswith(".java") else f"{p}.java")
    return names


def split_controller_name(class_name: str) -> tuple[str, str | None]:
    if not class_name.endswith("Controller"):
        return class_name, None
    stem = class_name[: -len("Controller")]
    for suffix in sorted(CHILD_CONTROLLER_SUFFIXES, key=len, reverse=True):
        if stem.endswith(suffix) and len(stem) > len(suffix):
            parent = stem[: -len(suffix)]
            if parent:
                return parent, suffix
    return stem, None


def _parse_controller(text: str, java_file: Path, repo_root: Path) -> ControllerInfo | None:
    if "@RestController" not in text:
        return None
    class_m = CLASS_RE.search(text)
    if not class_m:
        return None
    class_name = class_m.group(1)
    base = ""
    rm = REQUEST_MAPPING_RE.search(text)
    if rm:
        base = rm.group(1).rstrip("/")
    paths: list[str] = []
    for m in MAPPING_ANNOTATION.finditer(text):
        raw = m.group(1).strip()
        if raw:
            paths.append(raw)
    nested = tuple(p for p in paths if ID_SEGMENT_RE.search(p))
    rel = str(java_file.relative_to(repo_root)).replace("\\", "/")
    return ControllerInfo(
        class_name=class_name,
        path=java_file,
        rel_path=rel,
        base_mapping=base,
        http_paths=tuple(paths),
        nested_under_id=nested,
    )


def _iter_controller_files(repo_root: Path) -> list[Path]:
    base = repo_root / "src" / "main" / "java"
    if not base.is_dir():
        return []
    files: list[Path] = []
    for ctrl_dir in base.rglob("controller"):
        if ctrl_dir.is_dir():
            files.extend(ctrl_dir.glob("*.java"))
    return files


def _path_segment_to_field_hint(path: str) -> str | None:
    m = re.search(r"\{id[a-zA-Z]*\}/([a-z0-9-]+)", path)
    if not m:
        return None
    seg = m.group(1)
    parts = seg.split("-")
    if not parts:
        return None
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def _find_request_file(repo_root: Path, parent_stem: str) -> Path | None:
    base = repo_root / "src" / "main" / "java"
    if not base.is_dir():
        return None
    candidates = list(base.rglob(f"{parent_stem}Request.java"))
    return candidates[0] if candidates else None


def _find_service_file(repo_root: Path, parent_stem: str) -> Path | None:
    base = repo_root / "src" / "main" / "java"
    if not base.is_dir():
        return None
    candidates = list(base.rglob(f"{parent_stem}Service.java"))
    return candidates[0] if len(candidates) == 1 else None


def _check_aggregate_gaps(
    repo_root: Path,
    pair: DedicatedChildPair,
    parent: ControllerInfo,
) -> list[str]:
    notes: list[str] = []
    parent_stem = pair.parent_class.replace("Controller", "")
    fields: set[str] = set()
    for p in parent.nested_under_id:
        hint = _path_segment_to_field_hint(p)
        if hint:
            fields.add(hint)
    suffix_low = pair.child_suffix.lower()
    if "dependente" in suffix_low or "superior" in suffix_low:
        fields.add("clientesSuperiores")

    req_file = _find_request_file(repo_root, parent_stem)
    svc_file = _find_service_file(repo_root, parent_stem)
    if not req_file and not svc_file:
        return notes

    req_text = req_file.read_text(encoding="utf-8") if req_file and req_file.is_file() else ""
    svc_text = svc_file.read_text(encoding="utf-8") if svc_file and svc_file.is_file() else ""

    for fld in sorted(fields):
        if req_text and not re.search(rf"\b{re.escape(fld)}\b", req_text):
            req_name = req_file.name if req_file else f"{parent_stem}Request.java"
            notes.append(
                f"Possivel gap de agregado: `{pair.parent_class}` com sub-rota, mas `{req_name}` "
                f"sem campo `{fld}` (EV-MD-001)."
            )
            break

    if svc_text and not re.search(r"\b(sincronizar|substituir)\w*\s*\(", svc_text, re.IGNORECASE):
        notes.append(
            f"`{parent_stem}Service` sem chamada `sincronizar*`/`substituir*` visivel — "
            f"conferir escrita com `{pair.child_class}` (EV-MD-001)."
        )
    return notes[:3]


def analyze_repo(repo_root: Path) -> FilhoPaiAnalysis:
    allowlist = default_allowlist()
    by_class: dict[str, ControllerInfo] = {}
    for java_file in _iter_controller_files(repo_root):
        if java_file.name in allowlist:
            continue
        try:
            text = java_file.read_text(encoding="utf-8")
        except OSError:
            continue
        info = _parse_controller(text, java_file, repo_root)
        if info:
            by_class[info.class_name] = info

    analysis = FilhoPaiAnalysis()
    for class_name, child in by_class.items():
        parent_stem, suffix = split_controller_name(class_name)
        if suffix is None:
            continue
        parent_class = f"{parent_stem}Controller"
        parent = by_class.get(parent_class)
        if parent is None:
            continue
        pair = DedicatedChildPair(
            parent_class=parent_class,
            child_class=class_name,
            parent_rel=parent.rel_path,
            child_rel=child.rel_path,
            child_suffix=suffix,
            parent_nested_paths=parent.nested_under_id,
        )
        analysis.dedicated_children.append(pair)
        analysis.aggregate_notes.extend(_check_aggregate_gaps(repo_root, pair, parent))

    analysis.dedicated_children.sort(key=lambda p: p.child_rel)
    return analysis


def format_code_facts_markdown(analysis: FilhoPaiAnalysis) -> str:
    if not analysis.has_findings():
        return ""
    lines = [
        "## Fatos do codigo (mestre-filho, analise automatica)",
        "",
        "Use como evidencia obrigatoria; nao marque [x] nem `Nenhum.` em Importante se contradizer.",
        "",
    ]
    if analysis.dedicated_children:
        lines.append("### Controllers dedicados do filho (EV-MD-004)")
        for p in analysis.dedicated_children:
            nested = ", ".join(f"`{x}`" for x in p.parent_nested_paths[:4]) or "(nenhuma sub-rota `/{id}/…` no pai)"
            lines.append(
                f"- **{p.child_class}** (`{p.child_rel}`) com pai **{p.parent_class}** — "
                f"sub-rotas no pai: {nested}. Padrao: handlers no pai, nao `@RestController` so do filho."
            )
        lines.append("")
    if analysis.aggregate_notes:
        lines.append("### Agregado / request do pai")
        for note in analysis.aggregate_notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
