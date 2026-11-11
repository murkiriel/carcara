"""O catalogo.json: o índice que quem usa os pacotes lê para saber o que baixar, de onde e como conferir.

    {
      "schema": 1,
      "build_id": "2026-10-01-2b7e7669",     a geração; também o nome da release
      "built_at": "2026-10-01T17:30:00Z",
      "generator_commit": "abc1234",
      "tileset": {"name": "protomaps-basemap", "version": "4.15.2", "extensions": []},
      "source": {"kind": "protomaps-build", "timestamp", "url", "checksum", "osm_timestamp"},
      "tile_format": "mvt",
      "tile_compression": "gzip",
      "release_url": "https://github.com/<repositório>/releases/download/2026-10-01-2b7e7669/",
      "attribution": "...",
      "resources": {"file", "bytes", "sha256"},
      "base": {"file", "bytes", "sha256", "tiles", "minzoom", "maxzoom", "bbox", "bbox_tiles"},
      "states": {"GO": {"name": "Goiás", ...os mesmos campos, "light": {"file", "bytes", "sha256", "tiles",
                                                                        "minzoom", "maxzoom"}}, ...}
    }

`bbox` = [lat_min, lon_min, lat_max, lon_max] da área que o pacote atende (o polígono da UF no IBGE; na base, o
país), em graus WGS84, arredondado para fora. `bbox_tiles` = a área que os tiles do zoom mais fundo do pacote cobrem:
é maior, porque o recorte leva a margem e os tiles passam da divisa. O GeoJSON e o cabeçalho do PMTiles usam
longitude primeiro; aqui é latitude primeiro, como nos catálogos dos projetos irmãos (decisão D13: a ordem fica e é
declarada em docs/ARQUITETURA.md e docs/CONSUMO.md).

`light` é opcional: uma geração sem pacotes leves não escreve a chave.

`contract` é o mesmo catálogo no formato comum aos quatro geradores irmãos (docs/CATALOGO.md, esquema em
docs/catalogo-v1.schema.json): só acrescenta, nenhuma chave acima muda. Sai inteiro das chaves acima e do config, então
dá para refazê-lo de um catálogo já publicado (scripts/recatalog.py).
"""
from __future__ import annotations

import json
import math
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from . import config, mvt, packs, resources, sources

SCHEMA = 1
TILESET_NAME = "protomaps-basemap"
SOURCE_KIND = "protomaps-build"
START_MARKER = "<!-- downloads:start -->"
END_MARKER = "<!-- downloads:end -->"

_FILE_KEYS = ("file", "bytes", "sha256", "tiles", "minzoom", "maxzoom")


def git_commit_full(revision: str = "HEAD") -> Optional[str]:
    """O SHA completo (40 dígitos) de `revision` no repositório, ou None fora de um checkout do git."""
    try:
        done = subprocess.run(["git", "-C", str(config.REPO), "rev-parse", "--verify", "--quiet",
                               f"{revision}^{{commit}}"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    sha = done.stdout.strip()
    return sha if done.returncode == 0 and len(sha) == 40 else None


def git_commit_hash() -> str:
    """Hash curto do commit do repositório, ou 'desconhecido' fora de um checkout do git."""
    try:
        done = subprocess.run(["git", "-C", str(config.REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "desconhecido"
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else "desconhecido"


def polygon_bbox(bounds) -> List[float]:
    """[lat mín, lon mín, lat máx, lon máx] de um retângulo (oeste, sul, leste, norte), arredondado para fora em 2
    casas: nunca menor que a área."""
    west, south, east, north = bounds
    return [math.floor(south * 100) / 100, math.floor(west * 100) / 100,
            math.ceil(north * 100) / 100, math.ceil(east * 100) / 100]


def tiles_bbox(bounds, zoom: int) -> List[float]:
    """A área coberta pelos tiles do `zoom` que tocam o retângulo (oeste, sul, leste, norte), na mesma ordem do
    `bbox`, arredondada para fora em 4 casas."""
    west, south, east, north = bounds
    left, top = mvt.tile_at(north, west, zoom)
    right, bottom = mvt.tile_at(south, east, zoom)
    tile_west, _, _, tile_north = mvt.tile_bounds(zoom, left, top)
    _, tile_south, tile_east, _ = mvt.tile_bounds(zoom, right, bottom)
    return [math.floor(tile_south * 1e4) / 1e4, math.floor(tile_west * 1e4) / 1e4,
            math.ceil(tile_north * 1e4) / 1e4, math.ceil(tile_east * 1e4) / 1e4]


def _country_bounds(polygons: Dict[str, object]):
    boxes = [polygon.bounds for polygon in polygons.values()]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _entry(pack: dict, area_bounds) -> dict:
    entry = {key: pack[key] for key in _FILE_KEYS}
    entry["bbox"] = polygon_bbox(area_bounds)
    entry["bbox_tiles"] = tiles_bbox(pack["bounds"], int(pack["maxzoom"]))
    return entry


def build_catalog(build: Dict[str, object], generated: Dict[str, dict], resources_pack: Dict[str, object],
                  polygons: Dict[str, object], osm_timestamp: str, built_at: Optional[str] = None,
                  generator_commit: Optional[str] = None, generator_commit_full: Optional[str] = None) -> dict:
    """O catálogo de uma geração: `generated` é o que o `packs.generate` devolve; `polygons`, a malha das UFs.
    `generator_commit` (curto) e `generator_commit_full` (40 dígitos) vêm do git quando não são dados; um SHA completo em
    `generator_commit` vale para os dois."""
    if generator_commit_full is None:
        if generator_commit and len(generator_commit) == 40:
            generator_commit_full = generator_commit
        elif not generator_commit:
            generator_commit_full = git_commit_full()
    build_id = sources.build_id(build)
    states = {}
    for state in sorted(name for name in generated if name != packs.BASE):
        pack = generated[state]
        entry = {"name": config.STATES[state], **_entry(pack, polygons[state].bounds)}
        if pack.get("light"):
            entry["light"] = {key: pack["light"][key] for key in _FILE_KEYS}
        states[state] = entry
    cat = {
        "schema": SCHEMA,
        "build_id": build_id,
        "built_at": built_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator_commit": generator_commit or git_commit_hash(),
        "tileset": {"name": TILESET_NAME, "version": str(build["version"]), "extensions": []},
        "source": {"kind": SOURCE_KIND, "timestamp": str(build["uploaded"]), "url": str(build["url"]),
                   "checksum": str(build["b3sum"]), "osm_timestamp": osm_timestamp},
        "tile_format": "mvt",
        "tile_compression": "gzip",
        "release_url": config.RELEASE_URL.format(tag=build_id),
        "attribution": config.ATTRIBUTION,
        "resources": {key: resources_pack[key] for key in ("file", "bytes", "sha256")},
        "base": _entry(generated[packs.BASE], _country_bounds(polygons)),
        "states": states,
    }
    cat["contract"] = contract(cat, generator_commit_full)
    return cat


# O contrato de catálogo comum (docs/CATALOGO.md). Os nomes e valores fixos são os da especificação v1.
CONTRACT_NAME = "catalogo-comum"
CONTRACT_VERSION = 1
CONTRACT_MIN_READER_VERSION = 1
DATASET = "carcara"
BBOX_ORDER = "lat_min,lon_min,lat_max,lon_max"
RESOURCES_ID = "recursos"
LIGHT_SUFFIX = "-leve"
PMTILES_MEDIA_TYPE = "application/vnd.pmtiles"
RESOURCES_FORMAT = "glyphs-sprites"
# Reservado para o estilo pronto (docs/CATALOGO.md, Carcará): ainda não publicado.
STYLE_FORMAT = "maplibre-style"

# As constantes do config que descrevem as entradas da geração (`sources`). O scripts/recatalog.py troca pelas do config
# no commit que gerou a geração, para não atribuir a ela um checksum que veio depois.
SOURCE_CONSTANTS = ("IBGE_MESH_URL", "IBGE_MESH_COPY_SHA256", "IBGE_MESH_COPY_DATE", "ASSETS_REVISION",
                    "ASSETS_ARCHIVE_URL", "ASSETS_CONTENT_SHA256")


def config_sources() -> Dict[str, str]:
    return {name: getattr(config, name) for name in SOURCE_CONSTANTS}


def _sources(cat: dict, constants: Mapping[str, str]) -> list:
    source = cat["source"]
    sources = [{"id": "protomaps-build", "name": "Protomaps, build diário do basemap (OpenStreetMap)",
                "url": source["url"], "date": source["timestamp"], "version": cat["tileset"]["version"],
                "license": "ODbL-1.0", "checksums": {"b3sum": source["checksum"]}}]
    if constants.get("IBGE_MESH_COPY_SHA256"):
        sources.append({"id": "ibge-malha-uf", "name": "IBGE, malha das UFs (cópia versionada no repositório)",
                        "url": constants.get("IBGE_MESH_URL"), "date": constants.get("IBGE_MESH_COPY_DATE"),
                        "license": None, "checksums": {"sha256": constants["IBGE_MESH_COPY_SHA256"]}})
    revision = constants.get("ASSETS_REVISION")
    if revision and constants.get("ASSETS_CONTENT_SHA256"):
        url = constants.get("ASSETS_ARCHIVE_URL")
        sources.append({"id": "protomaps-basemaps-assets", "name": "Protomaps, fontes e ícones do basemap",
                        "url": url.format(revision=revision) if url else None, "date": None, "version": revision,
                        "license": config.RESOURCES_LICENSE,
                        "checksums": {"sha256": constants["ASSETS_CONTENT_SHA256"]},
                        "note": "sha256 do conteúdo que entra no pacote de recursos (resources.content_digest), "
                                "não do arquivo baixado"})
    return sources


def _tiles_file(file_id: str, kind: str, region: str, entry: dict, bbox: List[float], release_url: str) -> dict:
    return {
        "id": file_id, "kind": kind, "region": region, "url": release_url + entry["file"],
        "sha256": entry["sha256"], "bytes": entry["bytes"], "bytes_unpacked": None,
        "media_type": PMTILES_MEDIA_TYPE, "unpack": [], "format": "pmtiles",
        "bbox": list(bbox),
        "coverage_level": "BASE_HIGHWAYS_ONLY" if kind == "base" else "DETAILED",
        "requires": [RESOURCES_ID],
        "minzoom": entry["minzoom"], "maxzoom": entry["maxzoom"], "tiles": entry["tiles"],
    }


def _files(cat: dict) -> List[dict]:
    release_url = cat["release_url"]
    base = cat["base"]
    files = [_tiles_file("base", "base", "BR", base, base["bbox"], release_url)]
    for state, entry in sorted(cat["states"].items()):
        files.append(_tiles_file(state, "uf", state, entry, entry["bbox"], release_url))
        if entry.get("light"):
            files.append(_tiles_file(state + LIGHT_SUFFIX, "uf_light", state, entry["light"], entry["bbox"],
                                     release_url))
    pack = cat["resources"]
    files.append({"id": RESOURCES_ID, "kind": "resources", "region": None, "url": release_url + pack["file"],
                  "sha256": pack["sha256"], "bytes": pack["bytes"], "bytes_unpacked": None,
                  "media_type": "application/gzip", "unpack": ["gzip", "tar"], "format": RESOURCES_FORMAT,
                  "bbox": None, "coverage_level": None, "requires": [], "license": config.RESOURCES_LICENSE})
    return files


def compatibility(cat: dict) -> dict:
    """O bloco `compatibility`: o esquema dos tiles, o formato do arquivo e onde estão as fontes e os ícones."""
    version = cat["tileset"]["version"]
    return {
        "mix_generations": True,
        "data_format": {"name": "pmtiles", "version": str(config.PMTILES_SPEC_VERSION)},
        DATASET: {
            "tileset": {"name": cat["tileset"]["name"], "version": version, "major": int(version.split(".")[0])},
            "pmtiles_version": config.PMTILES_SPEC_VERSION,
            "tile_type": cat["tile_format"],
            "tile_compression": cat["tile_compression"],
            "glyphs": {"file": RESOURCES_ID, "template": "fonts/{fontstack}/{range}.pbf",
                       "fontstacks": list(resources.FONTSTACKS)},
            "sprites": {"file": RESOURCES_ID, "template": resources.SPRITES_FOLDER + "{flavor}",
                        "flavors": list(resources.SPRITE_FLAVORS)},
        },
    }


def contract(cat: dict, generator_commit_full: Optional[str],
             source_constants: Optional[Mapping[str, str]] = None) -> dict:
    """O bloco `contract` (docs/CATALOGO.md) a partir das chaves antigas do catálogo `cat` e do config. Recusa um
    catálogo de outra versão maior do esquema: as fontes e os ícones descritos seriam os da versão do config."""
    if cat["tileset"]["version"].split(".")[0] != str(config.TILESET_MAJOR_VERSION):
        raise ValueError(f"catálogo do esquema {cat['tileset']['version']}, o config é da versão maior "
                         f"{config.TILESET_MAJOR_VERSION}")
    if generator_commit_full is not None and not generator_commit_full.startswith(cat["generator_commit"]):
        raise ValueError(f"o commit {generator_commit_full} não é o {cat['generator_commit']} do catálogo")
    return {
        "name": CONTRACT_NAME,
        "version": CONTRACT_VERSION,
        "min_reader_version": CONTRACT_MIN_READER_VERSION,
        "dataset": DATASET,
        "build_id": cat["build_id"],
        "built_at": cat["built_at"],
        "release_url": cat["release_url"],
        "generator": {"repository": config.REPOSITORY_URL, "commit": generator_commit_full},
        "license": {"data": config.DATA_LICENSE, "code": config.CODE_LICENSE, "attribution": cat["attribution"]},
        "coordinates": {"crs": "EPSG:4326", "bbox_order": BBOX_ORDER},
        "osm_snapshot": {"date": cat["source"]["osm_timestamp"], "md5": None},
        "sources": _sources(cat, config_sources() if source_constants is None else source_constants),
        "compatibility": compatibility(cat),
        "files": _files(cat),
    }


def save(catalog: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _strip_accents(text: str) -> str:
    """A chave de ordem dos nomes: sem acento e sem caixa ("Rio de Janeiro" antes de "Rio Grande do Norte")."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def _mb(size: int) -> str:
    return f"{size / 1e6:.1f}".replace(".", ",") + " MB"


def _link(catalog: dict, entry: Optional[dict]) -> str:
    """As duas células de um arquivo: o link para a release desta geração e o tamanho."""
    if not entry:
        return " | "
    return f"[{entry['file']}]({catalog['release_url']}{entry['file']}) | {_mb(entry['bytes'])}"


def downloads_table(catalog: dict) -> str:
    """A tabela de downloads do README: a base primeiro, depois as UFs pelo nome, com o completo e o leve de cada uma
    e o link direto para o arquivo na release desta geração."""
    source, resources_pack = catalog["source"], catalog["resources"]
    lines = [
        f"Geração **{catalog['build_id']}**: build da Protomaps de {source['timestamp'][:10]}, com dados do "
        f"OpenStreetMap de {source['osm_timestamp'][:10]}, no esquema {catalog['tileset']['version']}. Confira o "
        f"sha256 de cada arquivo pelo [`catalogo.json`](catalogo.json).",
        "",
        f"Ícones e fontes: [{resources_pack['file']}]({catalog['release_url']}{resources_pack['file']}) "
        f"({_mb(resources_pack['bytes'])}).",
        "",
        "| Pacote | Completo (até o zoom 15) | Tamanho | Leve (até o zoom 13) | Tamanho |",
        "|---|---|---:|---|---:|",
        f"| **Base** (o país até o zoom {catalog['base']['maxzoom']}) | {_link(catalog, catalog['base'])} | "
        f"{_link(catalog, None)} |",
    ]
    for state, entry in sorted(catalog["states"].items(), key=lambda item: _strip_accents(item[1]["name"])):
        lines.append(f"| {entry['name']} ({state}) | {_link(catalog, entry)} | {_link(catalog, entry.get('light'))} |")
    return "\n".join(lines)


def update_readme(text: str, table: str) -> str:
    """Troca só o que está entre os marcadores de downloads do README."""
    start, end = text.find(START_MARKER), text.find(END_MARKER)
    if start < 0 or end < start:
        raise ValueError(f"o README não tem os marcadores {START_MARKER} e {END_MARKER}")
    return text[:start + len(START_MARKER)] + "\n" + table + "\n" + text[end:]
