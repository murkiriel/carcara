# Estilos prontos

O pacote de recursos (`carcara-recursos.tar.gz`) traz estilos MapLibre prontos para desenhar os pacotes do
Carcará: claro, escuro e mais três variações, com rótulos em português e prédios em 3D. O aplicativo só precisa
dizer onde estão os recursos e os tiles. Este documento diz o que vem, como usar, como trocar os endereços, como
combinar pacotes e de onde vem o desenho. O uso geral dos pacotes está em [`CONSUMO.md`](CONSUMO.md).

Os estilos entram no pacote de recursos a partir da primeira geração feita com este código; o pacote das gerações
anteriores não os tem.

## O que vem

Dentro do `carcara-recursos.tar.gz`, além do que já havia (nada mudou de lugar nem de conteúdo):

```
styles/light.json        Carcará claro
styles/dark.json         Carcará escuro
styles/white.json        Carcará branco      (sem pontos de interesse)
styles/grayscale.json    Carcará cinza       (sem pontos de interesse)
styles/black.json        Carcará preto       (sem pontos de interesse)
styles/LICENCA.md        licenças dos estilos e dos ícones próprios
sprites/carcara-v4/      as folhas light e dark de sprites/v4/, com dois ícones próprios no fim, em 1x e 2x
```

O que os estilos fazem:

- **Rótulos em português:** todo nome é `name:pt` e, na falta, `name` (o nome local). As siglas dos estados no
  zoom baixo continuam vindo de `ref`.
- **Prédios em 3D:** a camada `buildings_3d` (`fill-extrusion`) aparece no zoom 14 e cresce até a altura cheia no
  zoom 15, enquanto a planta plana (`buildings`) some. A altura é `height` do tile; sem ela, **5 m**, um andar
  com folga (no Plano Piloto e arredores, 99% dos prédios têm `height`, e a mediana é 4 m). A base é
  `min_height`, ou o chão. A camada fica acima de vias e limites e abaixo de todos os rótulos, então funciona com
  a câmera inclinada (`pitch`). Para desligar, esconder a camada `buildings_3d` e tirar o `maxzoom` da `buildings`.
- **Ícones próprios:** posto de combustível (`fuel`) e prefeitura (`townhall`), nas variações claro e escuro. O
  posto entrou na lista de pontos de interesse do estilo, com a cor dos transportes; a prefeitura já estava na
  lista do estilo de referência, mas a folha de ícones de origem não tinha o desenho.
- **Só o que o pacote tem:** as nove camadas do esquema, as três fontes (Noto Sans Regular, Medium e Italic) e os
  ícones das folhas. A geração confere isso antes de publicar (ver "Travas").

As variações branco, cinza e preto não desenham pontos de interesse, como no estilo de referência, e usam as
folhas de `sprites/v4/` direto.

## Como usar

Cada estilo tem **dois modelos** que o aplicativo troca antes de entregar o estilo ao MapLibre:

| Modelo | Onde aparece | Trocar por |
|---|---|---|
| `{recursos}` | `glyphs` e `sprite` | o endereço da pasta onde o `carcara-recursos.tar.gz` foi aberto, sem barra no fim |
| `{tiles}` | `sources.carcara.url` | o endereço da fonte de tiles: um `pmtiles://...` ou uma TileJSON |

Os modelos aparecem só nesses três campos:

```json
"sources": { "carcara": { "type": "vector", "url": "{tiles}", "attribution": "..." } },
"glyphs": "{recursos}/fonts/{fontstack}/{range}.pbf",
"sprite": "{recursos}/sprites/carcara-v4/light"
```

`{fontstack}` e `{range}` **ficam como estão**: são do MapLibre. O caminho mais seguro é ler o JSON e trocar os três
campos no objeto; trocar no texto também serve, desde que o endereço não tenha aspas nem barra invertida (que
estragariam o JSON). Por que modelos e não caminhos relativos: o MapLibre não resolve `glyphs` e `sprite`
relativos ao endereço do estilo, e cada aplicativo serve os arquivos de um jeito (arquivo local, asset, servidor
local, web).

Exemplos de `{recursos}`: `file:///data/.../files/recursos` (pasta do aplicativo), `asset://recursos` (dentro do
APK), `http://127.0.0.1:8080` (servidor local), `https://exemplo.org/carcara` (web).

Exemplos de `{tiles}`: `pmtiles://file:///data/.../files/carcara-DF.pmtiles`, `pmtiles://https://exemplo.org/carcara-DF.pmtiles`,
`http://127.0.0.1:8080/carcara.json` (uma TileJSON do servidor local) ou `carcara://pacotes` (protocolo próprio
na web; ver abaixo).

### MapLibre Android, com arquivos locais

Um pacote só, lido direto do arquivo (o MapLibre lê PMTiles desde a versão 11.7.0):

```kotlin
val recursos = File(context.filesDir, "recursos")          // onde o carcara-recursos.tar.gz foi aberto
val pacote = File(context.filesDir, "carcara-DF.pmtiles")

val estilo = JSONObject(File(recursos, "styles/light.json").readText())
val base = "file://" + recursos.absolutePath
estilo.put("glyphs", estilo.getString("glyphs").replace("{recursos}", base))
estilo.put("sprite", estilo.getString("sprite").replace("{recursos}", base))
estilo.getJSONObject("sources").getJSONObject("carcara").put("url", "pmtiles://file://" + pacote.absolutePath)

map.setStyle(Style.Builder().fromJson(estilo.toString()))
```

Com mais de um estado, ou com a base junto, use o servidor local (próxima seção) e troque `{tiles}` pelo endereço
da TileJSON dele. Os cuidados do Android com o servidor local (HTTP sem criptografia em `127.0.0.1` e
`MapLibre.setConnected(true)`) estão em [`CONSUMO.md`](CONSUMO.md).

**Não conferido:** este exemplo não foi rodado num aparelho. A leitura `pmtiles://file://` foi conferida no
MapLibre 13.4.1 para Android (CONSUMO.md), mas as fontes e os ícones por `file://` não: os nomes das pastas de
fontes têm espaço (`Noto Sans Regular`). Se os rótulos não aparecerem, sirva `fonts/` e `sprites/` pelo servidor
local e use `http://127.0.0.1:<porta>` como `{recursos}`.

### Web, com pmtiles.js

Um pacote só:

```js
const protocolo = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocolo.tile);

const estilo = await (await fetch("/recursos/styles/light.json")).json();
const recursos = new URL("/recursos", location.href).href;
estilo.glyphs = estilo.glyphs.replace("{recursos}", recursos);
estilo.sprite = estilo.sprite.replace("{recursos}", recursos);
estilo.sources.carcara.url = "pmtiles://" + new URL("/tiles/carcara-DF.pmtiles", location.href).href;

new maplibregl.Map({ container: "mapa", style: estilo });
```

O servidor precisa aceitar pedidos por faixa (`Range`), como diz o CONSUMO.md.

## Combinar pacotes: a base e um ou mais estados

Os estilos têm **uma fonte só**, `carcara`. Para desenhar a base e vários estados com o mesmo estilo, o aplicativo
junta os pacotes atrás dessa fonte: para cada tile pedido, procura nos pacotes de estado e depois na base, e
entrega o primeiro que achar. É o caminho que o [`CONSUMO.md`](CONSUMO.md) recomenda (servidor local), e o
estilo não muda com o número de estados.

O padrão:

- **Ordem de busca:** os estados instalados (qualquer ordem: um tile de divisa é o mesmo nos dois pacotes da mesma
  geração), depois a base.
- **TileJSON:** `minzoom` 0 e `maxzoom` 15. Com só pacotes leves instalados, `maxzoom` 13.
- **Tile que não está em nenhum pacote:** resposta vazia (no servidor local, 204 ou 404), nunca um erro que pare o
  mapa.
- **Compressão:** os tiles dos pacotes estão em gzip; o servidor local entrega com `Content-Encoding: gzip` ou
  descompacta antes.

### No aplicativo (servidor local)

O servidor responde `/carcara.json` com uma TileJSON e `/{z}/{x}/{y}.mvt` com o tile:

```json
{
  "tilejson": "3.0.0",
  "tiles": ["http://127.0.0.1:8080/{z}/{x}/{y}.mvt"],
  "minzoom": 0,
  "maxzoom": 15,
  "attribution": "<o campo attribution dos metadados de um pacote>"
}
```

e o aplicativo troca `{tiles}` por `http://127.0.0.1:8080/carcara.json`. O mesmo servidor pode entregar `fonts/` e
`sprites/`, e aí `{recursos}` vira `http://127.0.0.1:8080`.

### Na web (protocolo próprio)

O mesmo padrão, sem servidor de tiles, com um protocolo do MapLibre GL JS. É o código das capturas de tela que
conferiram os estilos (DF e base juntos):

```js
const pacotes = ["carcara-DF.pmtiles", "carcara-GO.pmtiles", "carcara-base.pmtiles"]
  .map((nome) => new pmtiles.PMTiles(new URL("/tiles/" + nome, location.href).href));

maplibregl.addProtocol("carcara", async (params, abort) => {
  if (params.type === "json") {
    return { data: { tilejson: "3.0.0", tiles: ["carcara://{z}/{x}/{y}"], minzoom: 0, maxzoom: 15 } };
  }
  const [z, x, y] = params.url.slice("carcara://".length).split("/").map(Number);
  for (const pacote of pacotes) {
    const tile = await pacote.getZxy(z, x, y, abort.signal);   // o pmtiles.js já descompacta
    if (tile) return { data: new Uint8Array(tile.data) };
  }
  return { data: new Uint8Array() };
});

estilo.sources.carcara.url = "carcara://pacotes";
```

### O que a fonte única não faz

- **Fora dos estados instalados, acima do zoom 9, o mapa fica vazio.** A base vai só até o zoom 9, e a fonte
  declara `maxzoom` 15: o MapLibre pede o tile do zoom 12, que não existe em pacote nenhum, e não amplia o do 9
  sozinho. Quem quiser a base ampliada nessas áreas precisa que o servidor local recorte e reescale o tile do 9, ou
  limitar o zoom do mapa fora dos estados.
- **Pacote leve misturado com completo:** com `maxzoom` 15, a área de um estado leve fica vazia nos zooms 14 e 15.
- **Uma fonte por arquivo** (o segundo caminho do CONSUMO.md) também funciona com estes estilos, mas exige copiar
  cada camada para cada fonte, com `id` e `source` trocados, e desenha duas vezes onde os pacotes se sobrepõem.
  Não é o recomendado.

## Como os estilos são feitos

Os estilos são gerados pelo pacote npm [`@protomaps/basemaps`](https://github.com/protomaps/basemaps), o mesmo que
gera os estilos de referência do esquema. A versão é a **5.7.2** (a última publicada, de 2026-03-10; os estilos 5.x
são os do esquema 4.x dos tiles, e o 5.7.0 trouxe as folhas de ícones atuais). O script fica em
[`gerador/estilos/`](../gerador/estilos/):

```
gerador/estilos/
├── package.json        dependências diretas com a versão exata: @protomaps/basemaps e @resvg/resvg-js
├── package-lock.json   todas as dependências, com a versão e a integridade (sha512) de cada pacote
├── gerar.mjs           gera os estilos e desenha os ícones
├── icones/             os ícones próprios em SVG (cores da variação clara)
└── gerado/             o que o gerar.mjs produz: <variação>.json e icones/<ícone>-<variação>[@2x].png
```

Para gerar de novo, dentro de `gerador/estilos/`:

```
npm ci --ignore-scripts
node gerar.mjs              # grava gerado/
node gerar.mjs --conferir   # só confere que gerado/ é o que sai do script
```

O workflow de testes roda o `--conferir` a cada push: um estilo editado à mão, ou gerado com outra versão do
pacote, barra o teste. A geração semanal **não usa Node**: o gerador em Python lê `gerado/`, copia os estilos para
`styles/` e põe os ícones próprios no fim das folhas `light` e `dark` de origem (`carcara/styles.py`), de forma
reproduzível, byte a byte.

O que o `gerar.mjs` muda no que o pacote gera, além de dizer `{recursos}` e `{tiles}`:

- os nomes (nome local e nome em português em duas linhas, com recurso ao inglês nos países) viram
  `["coalesce", ["get", "name:pt"], ["get", "name"]]`; a fonte para a escrita devanágari, que o pacote de recursos
  não tem, sai junto;
- o ícone dos pontos de interesse e o dos escudos de rodovia passam a ser escritos por extenso (`match` com cada
  nome), em vez de montados do dado (`["get", "kind"]`, `concat` com o tamanho do texto): o resultado no mapa é o
  mesmo, e a trava de validação consegue conferir cada nome contra a folha de ícones;
- `fuel` entra na lista de pontos de interesse;
- a camada `buildings_3d` e a transição da planta plana.

Os ícones são SVGs próprios, desenhados do zero no mesmo formato dos de origem (quadrado arredondado de 19 px,
fundo claro e traço da cor do grupo), e passados a PNG pelo `@resvg/resvg-js` em 19 e 38 px.

Trocar a versão do `@protomaps/basemaps`: mudar no `package.json`, `npm install`, `node gerar.mjs`, conferir as
capturas e os testes. Se o pacote mudar de forma, o `gerar.mjs` para com erro em vez de gerar um estilo errado.

## Travas

A trava de recursos da geração ([`validation.py`](../gerador/carcara/validation.py)) abre o
`carcara-recursos.tar.gz` montado e confere, para cada estilo de `styles/`:

- é JSON válido e um estilo MapLibre (`"version": 8`), com ids de camada únicos;
- tem só a fonte `carcara`, vetorial, com `url` igual a `{tiles}` e o crédito igual ao dos pacotes;
- `glyphs` e `sprite` usam `{recursos}`, e a folha de ícones citada está no pacote, em 1x e 2x;
- toda camada lê a fonte `carcara` e uma das nove camadas do esquema;
- toda fonte citada (inclusive dentro de `format`) é uma pasta de `fonts/` do pacote, uma por lista;
- todo ícone citado existe na folha do estilo, em 1x e 2x; um ícone que dependa do dado e não possa ser listado é
  recusado.

E confere que as folhas de `sprites/carcara-v4/` têm os ícones de origem e os próprios, dentro da imagem. Os testes
unitários (`tests/test_styles.py`) fazem a mesma conferência sobre `gerado/` e cobrem cada caso de recusa.

## Licença e atribuição

- **Estilos:** gerados pelo `@protomaps/basemaps`, código sob a licença BSD de 3 cláusulas ("Copyright 2019-2023
  Protomaps LLC, Kelso Cartography"); o desenho visual dos estilos da Protomaps é CC0. O texto vai em
  `styles/LICENCA.md` dentro do pacote, e a origem fica em `metadata` de cada estilo
  (`"carcara:origem": "@protomaps/basemaps 5.7.2"`).
- **Ícones de origem** (`sprites/v4/` e a parte de cima das folhas de `sprites/carcara-v4/`): derivados de um
  conjunto MIT, como já estava (`sprites/LICENCA.md`).
- **Ícones próprios** (`fuel` e `townhall`): desenhos do Carcará, sob a licença MIT do código do gerador.
- **Os dados** continuam pedindo o crédito do `attribution` do catálogo. Os estilos já levam o crédito dos pacotes
  na fonte `carcara`, que o MapLibre mostra no canto do mapa; com uma TileJSON própria, ponha o mesmo texto nela.

## O que foi conferido e o que não foi

- Conferido em 2026-11-11, com os pacotes reais do DF e da base da geração `2026-11-09-486b0133`, no MapLibre GL JS
  5.6.0 com o pmtiles.js 4.3.0, num Chrome sem tela: claro e escuro no zoom 12 e no zoom 16 com câmera inclinada e
  prédios em 3D sobre a Esplanada dos Ministérios; os ícones de posto e de prefeitura no Plano Piloto; a base e o DF
  juntos pelo protocolo próprio (zoom 8); o pacote do DF sozinho pelo `pmtiles://` (zoom 14,5); e as variações
  branco, cinza e preto inclinadas no zoom 15,5. Nenhum erro, nenhum ícone faltando. Os cinco estilos também
  passam no validador do `@maplibre/maplibre-gl-style-spec` 23.3.0 sem nenhum aviso.
- Não conferido: os estilos no MapLibre para Android e iOS, e a leitura de fontes e ícones por `file://` e
  `asset://`.
- Prédio com partes (`building` e `building_part` no mesmo lugar) é extrudado duas vezes, como no estilo de
  referência; onde as alturas coincidem, o teto pode piscar.
- Os tiles não têm superfície de via (pavimentada ou não); os estilos não distinguem.
