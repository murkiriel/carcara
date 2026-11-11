// Gera os estilos MapLibre do pacote de recursos e os ícones próprios, a partir do @protomaps/basemaps.
//
//   npm ci && node gerar.mjs              grava gerado/<variação>.json e gerado/icones/*.png
//   npm ci && node gerar.mjs --conferir   só confere que o que está no repositório é o que sai daqui
//
// As versões são as do package-lock.json (versão exata e integridade de cada pacote). O gerador em Python não roda
// este script: ele lê o que está em gerado/ e põe no carcara-recursos.tar.gz. Ver docs/ESTILOS.md.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { get_country_name, get_multiline_name, layers, namedFlavor } from "@protomaps/basemaps";
import { Resvg } from "@resvg/resvg-js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, "gerado");
const BASEMAPS_VERSION = JSON.parse(
  fs.readFileSync(path.join(HERE, "node_modules", "@protomaps", "basemaps", "package.json"), "utf-8"),
).version;

// Os modelos que o aplicativo troca ao carregar o estilo (docs/ESTILOS.md).
const RESOURCES = "{recursos}";
const TILES = "{tiles}";
const SOURCE = "carcara";

// As variações de cor, com o mesmo nome das folhas de ícones. Só `light` e `dark` têm pontos de interesse: elas
// usam a folha do Carcará (sprites/carcara-v4/), que é a de origem com os ícones próprios no fim.
const FLAVORS = {
  light: "Carcará claro",
  dark: "Carcará escuro",
  white: "Carcará branco",
  grayscale: "Carcará cinza",
  black: "Carcará preto",
};
const OWN_SPRITE_FLAVORS = ["light", "dark"];

// O crédito que o gerador grava em cada pacote (EMBEDDED_ATTRIBUTION em carcara/config.py; um teste confere).
const ATTRIBUTION =
  '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; colaboradores do OpenStreetMap</a> | ' +
  '<a href="https://esa-worldcover.org/" target="_blank">&copy; ESA WorldCover project 2020 / Contains modified ' +
  "Copernicus Sentinel data (2020) processed by ESA WorldCover consortium</a>";

// Rótulos em português: o nome em `name:pt` e, na falta, o nome local.
const NAME = ["coalesce", ["get", "name:pt"], ["get", "name"]];

// Prédios em 3D: a partir do zoom 14, crescendo até a altura cheia no 15. Sem `height`, a altura padrão.
const EXTRUSION_MINZOOM = 14;
const DEFAULT_HEIGHT = 5;
const EXTRUSION = {
  light: { color: "#d6d2cb", opacity: 0.9 },
  dark: { color: "#2b2b2e", opacity: 0.9 },
  white: { color: "#e4e4e4", opacity: 0.9 },
  grayscale: { color: "#d0d0d0", opacity: 0.9 },
  black: { color: "#1c1c1c", opacity: 0.9 },
};

// Ícones próprios: nome do ícone = `kind` do ponto de interesse. O SVG tem as cores da variação light; para a dark,
// as cores são trocadas por estas (as mesmas dos ícones de origem do mesmo grupo).
const OWN_ICONS = {
  fuel: { group: "transport", dark: { "#d7e4f2": "#202228", "#5c7ed8": "#284db8" } },
  townhall: { group: "civic", dark: { "#dcebfa": "#242425", "#8780ab": "#76767f" } },
};
const ICON_SIZE = 19;

const SHIELD_NETWORKS = ["US:I", "NL:S-road"];
const SHIELD_MAX_CHARS = 5;

// Troca, em qualquer ponto de uma expressão, os nomes que o pacote monta (nome local e nome no idioma, em uma ou
// duas linhas, e o nome de país com recurso ao inglês) pelo NAME. O resto da expressão fica como está.
function replaceNames(value, upstreamNames) {
  if (!Array.isArray(value)) return value;
  if (upstreamNames.has(JSON.stringify(value))) return NAME;
  return value.map((part) => replaceNames(part, upstreamNames));
}

// A lista literal de `kind` do filtro da camada de pontos de interesse.
function poiKinds(layer) {
  const condition = layer.filter.find(
    (part) => Array.isArray(part) && part[0] === "in" && JSON.stringify(part[1]) === '["get","kind"]',
  );
  if (!condition) throw new Error("a camada pois mudou de forma: não achei a lista de kind no filtro");
  return condition[2][1];
}

function adaptPois(layer) {
  const kinds = poiKinds(layer);
  for (const icon of Object.keys(OWN_ICONS)) if (!kinds.includes(icon)) kinds.push(icon);
  // A cor do texto: o posto vai com os transportes (o grupo do ponto de ônibus). A prefeitura já está na lista.
  const color = layer.paint["text-color"];
  const transport = color.findIndex(
    (part) => Array.isArray(part) && JSON.stringify(part).includes('"bus_stop"'),
  );
  if (transport < 0) throw new Error("a camada pois mudou de forma: não achei o grupo de cor dos transportes");
  if (!color[transport][2][1].includes("fuel")) color[transport][2][1].push("fuel");
  // O ícone de cada kind, por extenso: assim a trava de validação confere cada nome contra a folha de ícones.
  const icons = ["match", ["get", "kind"]];
  for (const kind of kinds) icons.push(kind, kind === "station" ? "train_station" : kind);
  icons.push("");
  layer.layout["icon-image"] = icons;
}

function adaptShields(layer) {
  const byLength = (prefix) => {
    const parts = ["match", ["length", ["get", "shield_text"]]];
    for (let chars = 1; chars <= SHIELD_MAX_CHARS; chars++) parts.push(chars, `${prefix}-${chars}char`);
    parts.push("");
    return parts;
  };
  const icons = ["match", ["get", "network"]];
  for (const network of SHIELD_NETWORKS) icons.push(network, byLength(network));
  icons.push(byLength("generic_shield"));
  layer.layout["icon-image"] = icons;
}

function buildings3d(flavor) {
  const height = ["max", ["coalesce", ["get", "height"], DEFAULT_HEIGHT], ["coalesce", ["get", "min_height"], 0]];
  const grow = (value) => ["interpolate", ["linear"], ["zoom"], EXTRUSION_MINZOOM, 0, EXTRUSION_MINZOOM + 1, value];
  return {
    id: "buildings_3d",
    type: "fill-extrusion",
    source: SOURCE,
    "source-layer": "buildings",
    minzoom: EXTRUSION_MINZOOM,
    filter: ["in", ["get", "kind"], ["literal", ["building", "building_part"]]],
    paint: {
      "fill-extrusion-color": EXTRUSION[flavor].color,
      "fill-extrusion-height": grow(height),
      "fill-extrusion-base": grow(["coalesce", ["get", "min_height"], 0]),
      "fill-extrusion-opacity": EXTRUSION[flavor].opacity,
      "fill-extrusion-vertical-gradient": true,
    },
  };
}

function style(flavor) {
  const theme = namedFlavor(flavor);
  const all = layers(SOURCE, theme, { lang: "pt" });
  const upstreamNames = new Set([
    JSON.stringify(get_multiline_name("pt", undefined, theme.regular)),
    JSON.stringify(get_country_name("pt")),
  ]);
  for (const layer of all) {
    const layout = layer.layout || {};
    if (layout["text-field"] !== undefined) layout["text-field"] = replaceNames(layout["text-field"], upstreamNames);
    if (layer.id === "pois") adaptPois(layer);
    if (layer.id === "roads_shields") adaptShields(layer);
    if (layer.id === "buildings") {
      // A planta plana some enquanto os prédios em 3D crescem.
      layer.maxzoom = EXTRUSION_MINZOOM + 1;
      layer.paint["fill-opacity"] = [
        "interpolate", ["linear"], ["zoom"], EXTRUSION_MINZOOM, layer.paint["fill-opacity"], EXTRUSION_MINZOOM + 1, 0,
      ];
    }
  }
  const text = JSON.stringify(all);
  for (const leftover of ['"name:en"', '"pgf:', "Devanagari"]) {
    if (text.includes(leftover)) throw new Error(`${flavor}: sobrou ${leftover} num rótulo; o pacote mudou de forma`);
  }
  // Os prédios em 3D ficam acima de vias e limites e abaixo de todos os rótulos.
  const firstSymbol = all.findIndex((layer) => layer.type === "symbol");
  all.splice(firstSymbol, 0, buildings3d(flavor));
  const sprites = OWN_SPRITE_FLAVORS.includes(flavor) ? "carcara-v4" : "v4";
  return {
    version: 8,
    name: FLAVORS[flavor],
    metadata: {
      "carcara:variacao": flavor,
      "carcara:esquema": "protomaps-basemap 4",
      "carcara:origem": `@protomaps/basemaps ${BASEMAPS_VERSION}`,
      "carcara:altura_padrao_predios": DEFAULT_HEIGHT,
    },
    sources: { [SOURCE]: { type: "vector", url: TILES, attribution: ATTRIBUTION } },
    glyphs: `${RESOURCES}/fonts/{fontstack}/{range}.pbf`,
    sprite: `${RESOURCES}/sprites/${sprites}/${flavor}`,
    layers: all,
  };
}

function icon(name, flavor, density) {
  let svg = fs.readFileSync(path.join(HERE, "icones", `${name}.svg`), "utf-8");
  if (flavor === "dark") {
    for (const [from, to] of Object.entries(OWN_ICONS[name].dark)) svg = svg.replaceAll(from, to);
  }
  const rendered = new Resvg(svg, { fitTo: { mode: "width", value: ICON_SIZE * density } }).render();
  return rendered.asPng();
}

function outputs() {
  const files = {};
  for (const flavor of Object.keys(FLAVORS)) {
    files[`${flavor}.json`] = Buffer.from(`${JSON.stringify(style(flavor), null, 2)}\n`, "utf-8");
  }
  for (const name of Object.keys(OWN_ICONS)) {
    for (const flavor of OWN_SPRITE_FLAVORS) {
      files[`icones/${name}-${flavor}.png`] = icon(name, flavor, 1);
      files[`icones/${name}-${flavor}@2x.png`] = icon(name, flavor, 2);
    }
  }
  return files;
}

const files = outputs();
if (process.argv.includes("--conferir")) {
  const different = Object.entries(files)
    .filter(([name, data]) => {
      const file = path.join(OUT, name);
      return !fs.existsSync(file) || !fs.readFileSync(file).equals(data);
    })
    .map(([name]) => name);
  if (different.length) {
    console.error(`diferente do que está em gerado/: ${different.join(", ")}`);
    process.exit(1);
  }
  console.log(`ok: os ${Object.keys(files).length} arquivos de gerado/ são os que este script produz`);
} else {
  for (const [name, data] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(OUT, name)), { recursive: true });
    fs.writeFileSync(path.join(OUT, name), data);
  }
  console.log(`gravados ${Object.keys(files).length} arquivos em gerado/`);
}
