"""O que vem de fora: o índice de builds da Protomaps e a malha das UFs do IBGE (a cópia versionada, conferida).

O build é escolhido sempre pelo índice (`builds.json`), nunca por um endereço montado com a data: a Protomaps guarda
os builds da última semana e avisa que os endereços podem mudar. Um build de outra versão maior do esquema é
recusado, para a troca de versão ser uma decisão e não um acidente.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

from . import config, net
from .util import file_hash

# Espera base entre tentativas, em segundos (multiplicada pelo número da tentativa). Os testes zeram.
RETRY_DELAY = 10

# O `key` do índice vira parte de um endereço e de nomes locais: só um nome de arquivo simples.
_BUILD_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.pmtiles$")
_REQUIRED_BUILD_FIELDS = ("key", "size", "b3sum", "uploaded", "version")


def latest_build() -> Dict[str, object]:
    """A entrada mais recente do índice de builds: {key, url, size, b3sum, uploaded, version}."""
    text = net.fetch_text(config.BUILDS_INDEX_URL, delay=RETRY_DELAY)
    try:
        index = json.loads(text)
    except ValueError as e:
        raise RuntimeError(f"o índice de builds não é JSON: {config.BUILDS_INDEX_URL}") from e
    entries = [e for e in index if isinstance(e, dict)] if isinstance(index, list) else []
    if not entries:
        raise RuntimeError(f"o índice de builds veio vazio ou em outro formato: {config.BUILDS_INDEX_URL}")
    entry = max(entries, key=lambda e: str(e.get("uploaded") or ""))
    missing = [field for field in _REQUIRED_BUILD_FIELDS if not entry.get(field)]
    if missing:
        raise RuntimeError(f"o build mais recente veio sem {', '.join(missing)}: {entry}")
    key, version = str(entry["key"]), str(entry["version"])
    if not _BUILD_KEY.match(key):
        raise RuntimeError(f"nome de build inesperado no índice: {key!r}")
    if version.split(".")[0] != str(config.TILESET_MAJOR_VERSION):
        raise RuntimeError(f"o build {key} é do esquema {version}; o gerador só aceita a versão maior "
                           f"{config.TILESET_MAJOR_VERSION}")
    return {"key": key, "url": config.BUILD_BASE_URL + key, "size": int(entry["size"]),
            "b3sum": str(entry["b3sum"]), "uploaded": str(entry["uploaded"]), "version": version}


_BUILD_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$")


def build_id(build: Dict[str, object]) -> str:
    """O nome da geração feita deste build: a data em que ele foi publicado e o começo do seu b3sum."""
    identifier = f"{str(build['uploaded'])[:10]}-{str(build['b3sum'])[:8]}"
    if not _BUILD_ID.match(identifier):
        raise ValueError(f"não dá para nomear a geração a partir deste build: {build}")
    return identifier


def mesh_problem(path: Path) -> Optional[str]:
    """O que há de errado com o arquivo da malha das UFs, ou None se é um GeoJSON com as 27 UFs.

    Uma API pode responder 200 com uma página de erro; sem esta conferência ela seria gravada e quebraria todas as
    gerações seguintes até alguém apagar o arquivo à mão."""
    try:
        gj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return f"não é JSON ({e.__class__.__name__})"
    features = gj.get("features") if isinstance(gj, dict) else None
    if not isinstance(features, list):
        return "sem a lista `features`"
    codes = {str((f.get("properties") or {}).get("codarea")) for f in features if isinstance(f, dict)}
    missing = sorted(state for code, state in config.IBGE_STATE_CODES.items() if code not in codes)
    return f"faltam as UFs {', '.join(missing)}" if missing else None


def ibge_mesh() -> Path:
    """A malha das UFs (GeoJSON das 27 UFs, código IBGE em `codarea`): a cópia versionada, config.IBGE_MESH_COPY,
    conferida pelas 27 UFs e pelo sha256 do config. Nada é baixado, como no Andorinha: a mesma malha gera sempre a
    mesma divisão dos pacotes, e a geração não depende da API do IBGE (que deixou de responder ao Actions em
    2026-11-04)."""
    copy = config.IBGE_MESH_COPY
    problem = mesh_problem(copy)
    if problem is not None:
        raise RuntimeError(f"a malha do IBGE em {copy.name} não serve ({problem})")
    sha256 = file_hash(copy, "sha256")
    if sha256 != config.IBGE_MESH_COPY_SHA256:
        raise RuntimeError(f"{copy.name} mudou (sha256 {sha256}, o config espera {config.IBGE_MESH_COPY_SHA256}): "
                           "uma malha nova muda a divisão dos pacotes; confira e atualize o IBGE_MESH_COPY_SHA256")
    print(f"[ibge] malha das UFs: {copy.name}, 27 UFs, sha256 confere")
    return copy
