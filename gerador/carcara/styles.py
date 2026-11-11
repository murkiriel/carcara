"""Os estilos MapLibre prontos e a folha de ícones do Carcará, que vão dentro do pacote de recursos.

Os estilos são gerados fora daqui, por `estilos/gerar.mjs` (Node, com o `@protomaps/basemaps` numa versão travada), e
ficam no repositório em `estilos/gerado/`: a geração só os copia para `styles/<variação>.json` do pacote. Os ícones
próprios (posto de combustível e prefeitura) também ficam lá, já em PNG; aqui eles são postos no fim das folhas
`light` e `dark` de origem, numa pasta à parte (`sprites/carcara-v4/`), sem mexer em `sprites/v4/`.

Os estilos não trazem endereço nenhum: `{recursos}` (a pasta onde o pacote de recursos foi aberto) e `{tiles}` (a
fonte dos tiles) são trocados pelo aplicativo. Ver docs/ESTILOS.md.

Aqui fica também a conferência de um estilo contra o pacote de recursos (`problems`), usada pela trava de recursos e
pelos testes: JSON válido, só camadas do esquema, só fontes que o pacote tem, só ícones que as folhas têm.
"""
from __future__ import annotations

import json
from typing import Dict, Iterable, List, Set, Tuple

from . import config, png

STYLES_DIR = config.GENERATOR_DIR / "estilos" / "gerado"
ICONS_DIR = STYLES_DIR / "icones"
LICENCE_SOURCE = config.GENERATOR_DIR / "licencas" / "ESTILOS.md"

# As variações de cor: as mesmas das folhas de ícones de origem.
FLAVORS = ("light", "dark", "white", "grayscale", "black")
STYLES_FOLDER = "styles/"
LICENCE = f"{STYLES_FOLDER}LICENCA.md"

# Os ícones próprios, com o nome igual ao `kind` do ponto de interesse, e as variações que desenham pontos de
# interesse (as únicas que ganham a folha do Carcará).
OWN_ICONS = ("fuel", "townhall")
OWN_SPRITE_FLAVORS = ("light", "dark")
UPSTREAM_SPRITES_FOLDER = f"sprites/v{config.TILESET_MAJOR_VERSION}/"
OWN_SPRITES_FOLDER = f"sprites/carcara-v{config.TILESET_MAJOR_VERSION}/"
DENSITIES = {"": 1, "@2x": 2}
# Folga, em pixels de 1x, entre a folha de origem e a fileira dos ícones próprios, e entre um ícone e outro.
GAP = 1

# As camadas do esquema protomaps-basemap 4.x que os pacotes têm (`vector_layers` dos metadados, versão 4.15.2).
SCHEMA_LAYERS = ("earth", "landcover", "landuse", "water", "buildings", "boundaries", "roads", "places", "pois")

# O que o aplicativo troca no estilo, e o nome da fonte de tiles.
RESOURCES_TOKEN = "{recursos}"
TILES_TOKEN = "{tiles}"
SOURCE = "carcara"
GLYPHS = RESOURCES_TOKEN + "/fonts/{fontstack}/{range}.pbf"

# Propriedades que pedem uma imagem da folha de ícones.
_IMAGE_PROPERTIES = ("icon-image", "fill-pattern", "line-pattern", "fill-extrusion-pattern", "background-pattern")
_BRANCHING = ("literal", "match", "case", "step", "coalesce", "image")


def style_file(flavor: str) -> str:
    return f"{STYLES_FOLDER}{flavor}.json"


def sprite_files(folder: str, flavor: str) -> List[str]:
    return [f"{folder}{flavor}{density}.{extension}" for density in DENSITIES for extension in ("json", "png")]


def required() -> List[str]:
    """Todo arquivo que os estilos acrescentam ao pacote de recursos."""
    names = [style_file(flavor) for flavor in FLAVORS] + [LICENCE]
    return names + [name for flavor in OWN_SPRITE_FLAVORS for name in sprite_files(OWN_SPRITES_FOLDER, flavor)]


def committed() -> Dict[str, bytes]:
    """{caminho no pacote: bytes} dos estilos que estão no repositório."""
    found = {}
    for flavor in FLAVORS:
        path = STYLES_DIR / f"{flavor}.json"
        if not path.is_file():
            raise RuntimeError(f"falta o estilo {path.name} em estilos/gerado/ (rodar estilos/gerar.mjs)")
        found[style_file(flavor)] = path.read_bytes()
    return found


def own_icon(name: str, flavor: str, density: str) -> png.Image:
    path = ICONS_DIR / f"{name}-{flavor}{density}.png"
    if not path.is_file():
        raise RuntimeError(f"falta o ícone {path.name} em estilos/gerado/icones/ (rodar estilos/gerar.mjs)")
    return png.decode(path.read_bytes())


def compose(sheet: png.Image, index: Dict[str, dict], icons: Iterable[Tuple[str, png.Image]],
            ratio: int) -> Tuple[png.Image, Dict[str, dict]]:
    """A folha `sheet` com os `icons` numa fileira nova embaixo, e o índice com as entradas novas."""
    icons = list(icons)
    repeated = [name for name, _ in icons if name in index]
    if repeated:
        raise RuntimeError(f"a folha de origem já tem os ícones {', '.join(repeated)}: tirar os próprios de "
                           f"estilos/gerar.mjs ou conferir qual vale")
    gap = GAP * ratio
    top = sheet.height + gap
    width = max(sheet.width, sum(icon.width for _, icon in icons) + gap * (len(icons) - 1))
    height = top + max((icon.height for _, icon in icons), default=0)
    result = png.Image(width, height)
    result.paste(sheet, 0, 0)
    entries = dict(index)
    x = 0
    for name, icon in icons:
        result.paste(icon, x, top)
        entries[name] = {"height": icon.height, "pixelRatio": ratio, "width": icon.width, "x": x, "y": top}
        x += icon.width + gap
    return result, entries


def own_sprites(files: Dict[str, bytes]) -> Dict[str, bytes]:
    """As folhas `sprites/carcara-v4/`: as de origem de `files`, com os ícones próprios acrescentados."""
    found = {}
    for flavor in OWN_SPRITE_FLAVORS:
        for density, ratio in DENSITIES.items():
            source = f"{UPSTREAM_SPRITES_FOLDER}{flavor}{density}"
            try:
                sheet = png.decode(files[f"{source}.png"])
                index = json.loads(files[f"{source}.json"].decode("utf-8"))
            except (KeyError, ValueError) as e:
                raise RuntimeError(f"não dá para ler a folha de ícones {source} ({e.__class__.__name__}: {e})") from e
            if not isinstance(index, dict):
                raise RuntimeError(f"o índice {source}.json não é um objeto")
            image, entries = compose(sheet, index, [(name, own_icon(name, flavor, density)) for name in OWN_ICONS],
                                     ratio)
            target = f"{OWN_SPRITES_FOLDER}{flavor}{density}"
            found[f"{target}.png"] = png.encode(image)
            found[f"{target}.json"] = (json.dumps(entries, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return found


def pack(files: Dict[str, bytes]) -> Dict[str, bytes]:
    """O que os estilos acrescentam ao pacote de recursos montado com `files`: estilos, folhas do Carcará e licença."""
    found = committed()
    found.update(own_sprites(files))
    found[LICENCE] = LICENCE_SOURCE.read_bytes()
    return found


class _Unknown(ValueError):
    """Uma expressão cujo resultado depende do dado: não dá para listar os valores possíveis."""


def _outputs(value) -> Set[str]:
    """Os textos que uma expressão de imagem pode dar. Só segue os ramos (match, case, step, coalesce)."""
    if isinstance(value, str):
        return {value}
    if not isinstance(value, list) or not value or value[0] not in _BRANCHING:
        raise _Unknown(json.dumps(value, ensure_ascii=False)[:80])
    op = value[0]
    if op == "literal":
        if isinstance(value[1], str):
            return {value[1]}
        raise _Unknown(json.dumps(value, ensure_ascii=False)[:80])
    if op == "image":
        branches = value[1:2]
    elif op == "match":
        branches = value[3:-1:2] + value[-1:]
    elif op == "case":
        branches = value[2:-1:2] + value[-1:]
    elif op == "step":
        branches = value[2::2]
    else:
        branches = value[1:]
    found: Set[str] = set()
    for branch in branches:
        found |= _outputs(branch)
    return found


def _fontstacks(value) -> Set[Tuple[str, ...]]:
    """As listas de fontes que um `text-font` pode dar."""
    if isinstance(value, list) and value and all(isinstance(part, str) for part in value) \
            and value[0] not in _BRANCHING:
        return {tuple(value)}
    if not isinstance(value, list) or not value or value[0] not in ("literal", "match", "case", "step"):
        raise _Unknown(json.dumps(value, ensure_ascii=False)[:80])
    op = value[0]
    if op == "literal":
        return _fontstacks(value[1])
    branches = value[3:-1:2] + value[-1:] if op == "match" else value[2:-1:2] + value[-1:] if op == "case" \
        else value[2::2]
    found: Set[Tuple[str, ...]] = set()
    for branch in branches:
        found |= _fontstacks(branch)
    return found


def _text_fonts(layout: dict) -> Iterable:
    """Todo `text-font` de um layout: o da propriedade e os de dentro das expressões `format`."""
    if "text-font" in layout:
        yield layout["text-font"]
    pending = [layout.get("text-field")]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if "text-font" in node:
                yield node["text-font"]
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)


def _sprite_index(files: Dict[str, bytes], base: str) -> Dict[str, Dict[str, dict]]:
    """{densidade: índice} da folha `base`; a densidade que falta ou não lê fica de fora."""
    found = {}
    for density in DENSITIES:
        try:
            index = json.loads(files[f"{base}{density}.json"].decode("utf-8"))
        except (KeyError, ValueError):
            continue
        if isinstance(index, dict):
            found[density] = index
    return found


def problems(name: str, data: bytes, files: Dict[str, bytes]) -> List[str]:
    """O que está errado no estilo `name` (bytes `data`) para o pacote de recursos com os arquivos `files`."""
    try:
        style = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        return [f"{name}: não é JSON válido ({e})"]
    if not isinstance(style, dict) or style.get("version") != 8:
        return [f"{name}: não é um estilo MapLibre (falta \"version\": 8)"]
    found = []

    sources = style.get("sources")
    expected = {SOURCE}
    if not isinstance(sources, dict) or set(sources) != expected:
        found.append(f"{name}: as fontes são {sorted(sources) if isinstance(sources, dict) else sources}; o esperado "
                     f"é só \"{SOURCE}\"")
    else:
        source = sources[SOURCE]
        if source.get("type") != "vector" or source.get("url") != TILES_TOKEN:
            found.append(f"{name}: a fonte \"{SOURCE}\" tem de ser vetorial, com \"url\": \"{TILES_TOKEN}\"")
        if source.get("attribution") != config.EMBEDDED_ATTRIBUTION:
            found.append(f"{name}: o crédito da fonte não é o que vai dentro dos pacotes")

    if style.get("glyphs") != GLYPHS:
        found.append(f"{name}: \"glyphs\" é {style.get('glyphs')!r}; o esperado é {GLYPHS!r}")
    fonts = {path.split("/")[1] for path in files if path.startswith("fonts/") and path.endswith(".pbf")}

    sprite = style.get("sprite")
    indexes: Dict[str, Dict[str, dict]] = {}
    if not isinstance(sprite, str) or not sprite.startswith(RESOURCES_TOKEN + "/"):
        found.append(f"{name}: \"sprite\" é {sprite!r}; o esperado é {RESOURCES_TOKEN}/sprites/...")
    else:
        base = sprite[len(RESOURCES_TOKEN) + 1:]
        missing = [path for path in sprite_files(base.rsplit("/", 1)[0] + "/", base.rsplit("/", 1)[-1])
                   if path not in files]
        if missing:
            found.append(f"{name}: a folha de ícones {base} não está no pacote (faltam {', '.join(missing)})")
        indexes = _sprite_index(files, base)

    layers = style.get("layers")
    if not isinstance(layers, list) or not layers:
        return found + [f"{name}: não tem camadas"]
    ids = [layer.get("id") for layer in layers if isinstance(layer, dict)]
    repeated = sorted({layer_id for layer_id in ids if ids.count(layer_id) > 1})
    if len(ids) != len(layers) or repeated:
        found.append(f"{name}: camadas sem id ou repetidas: {', '.join(map(str, repeated))}")

    wrong_layers, wrong_fonts, missing_icons, unknown = set(), set(), set(), []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = layer.get("id")
        if layer.get("type") != "background":
            if layer.get("source") != SOURCE:
                found.append(f"{name}: a camada {layer_id} lê a fonte {layer.get('source')!r}, não \"{SOURCE}\"")
            if layer.get("source-layer") not in SCHEMA_LAYERS:
                wrong_layers.add(f"{layer_id} ({layer.get('source-layer')})")
        layout, paint = layer.get("layout") or {}, layer.get("paint") or {}
        for value in _text_fonts(layout):
            try:
                stacks = _fontstacks(value)
            except _Unknown as e:
                unknown.append(f"text-font de {layer_id}: {e}")
                continue
            for stack in stacks:
                # O MapLibre pede as faixas de uma lista inteira de fontes de uma vez; o pacote tem uma por pasta.
                if len(stack) != 1 or stack[0] not in fonts:
                    wrong_fonts.add(", ".join(stack))
        for key in _IMAGE_PROPERTIES:
            value = layout.get(key, paint.get(key))
            if value is None:
                continue
            try:
                icons = _outputs(value) - {""}
            except _Unknown as e:
                unknown.append(f"{key} de {layer_id}: {e}")
                continue
            for density, index in indexes.items():
                missing_icons |= {f"{icon}{' (2x)' if density else ''}" for icon in icons if icon not in index}
    if wrong_layers:
        found.append(f"{name}: camadas que leem o que o esquema não tem: {', '.join(sorted(wrong_layers))}")
    if wrong_fonts:
        found.append(f"{name}: fontes que o pacote não tem: {', '.join(sorted(wrong_fonts))}")
    if missing_icons:
        found.append(f"{name}: ícones que a folha {sprite} não tem: {', '.join(sorted(missing_icons))}")
    if unknown:
        found.append(f"{name}: não dá para conferir, o valor depende do dado: {'; '.join(unknown[:3])}")
    return found
