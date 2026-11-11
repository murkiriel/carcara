# Carcará — mapa base do Brasil por estado, para uso offline

**Mapa base vetorial do Brasil em arquivos prontos para uso offline**: um pacote base (o país inteiro em zoom baixo),
um pacote por estado (até o zoom 15, e uma versão leve até o zoom 13) e um pacote de recursos (ícones e fontes).
Os arquivos são [PMTiles](https://docs.protomaps.com/pmtiles/), no esquema de camadas do
[basemap da Protomaps](https://docs.protomaps.com/basemaps/layers), recortados de novo toda semana, no domingo, do build
diário que a Protomaps gera do OpenStreetMap, e publicados como arquivos de release, com um `catalogo.json` na
raiz.

> **Aviso.** Os dados vêm do OpenStreetMap e podem estar incompletos ou errados.

**Índice:** [`catalogo.json`](catalogo.json) · **Pacotes:** [releases](https://github.com/Murkiriel/carcara/releases)
(a etiqueta de cada uma é o `build_id` da geração)

## Situação

Em 2026-11-11:

| Item | Como está |
|---|---|
| Geração publicada | `2026-11-09-486b0133`: build da Protomaps de 2026-11-09, dados do OpenStreetMap de 2026-11-09, esquema 4.15.2. A mais recente está sempre em [Baixar e usar](#baixar-e-usar) e no `built_at` do [`catalogo.json`](catalogo.json) |
| Próxima geração | Domingo, 2026-11-15: uma por semana ([Geração e reprodutibilidade](#geração-e-reprodutibilidade)) |
| Pacotes | 56 arquivos por geração, cerca de 6 GB com os leves, mais o `LICENCA-DADOS.txt` com a licença e a atribuição; os 27 completos somam cerca de 4,6 GB, o maior (MG) 595 MB |
| Gerações no ar | As 12 mais recentes (cerca de 3 meses); hoje são 3 |
| Formato | PMTiles, esquema Protomaps v4; catálogo no `schema` 1 |
| Repositório | Público desde 2026-10-05 |

## Baixar e usar

### Baixar por estado

<!-- downloads:start -->
Geração **2026-11-09-486b0133**: build da Protomaps de 2026-11-09, com dados do OpenStreetMap de 2026-11-09, no esquema 4.15.2. Confira o sha256 de cada arquivo pelo [`catalogo.json`](catalogo.json).

Ícones e fontes: [carcara-recursos.tar.gz](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-recursos.tar.gz) (6,2 MB).

| Pacote | Completo (até o zoom 15) | Tamanho | Leve (até o zoom 13) | Tamanho |
|---|---|---:|---|---:|
| **Base** (o país até o zoom 9) | [carcara-base.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-base.pmtiles) | 44,2 MB |  |  |
| Acre (AC) | [carcara-AC.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AC.pmtiles) | 62,3 MB | [carcara-AC-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AC-leve.pmtiles) | 20,1 MB |
| Alagoas (AL) | [carcara-AL.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AL.pmtiles) | 35,7 MB | [carcara-AL-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AL-leve.pmtiles) | 10,1 MB |
| Amapá (AP) | [carcara-AP.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AP.pmtiles) | 23,8 MB | [carcara-AP-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AP-leve.pmtiles) | 7,7 MB |
| Amazonas (AM) | [carcara-AM.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AM.pmtiles) | 213,7 MB | [carcara-AM-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-AM-leve.pmtiles) | 64,3 MB |
| Bahia (BA) | [carcara-BA.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-BA.pmtiles) | 296,4 MB | [carcara-BA-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-BA-leve.pmtiles) | 77,2 MB |
| Ceará (CE) | [carcara-CE.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-CE.pmtiles) | 159,7 MB | [carcara-CE-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-CE-leve.pmtiles) | 31,7 MB |
| Distrito Federal (DF) | [carcara-DF.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-DF.pmtiles) | 48,1 MB | [carcara-DF-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-DF-leve.pmtiles) | 7,1 MB |
| Espírito Santo (ES) | [carcara-ES.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-ES.pmtiles) | 364,5 MB | [carcara-ES-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-ES-leve.pmtiles) | 124,9 MB |
| Goiás (GO) | [carcara-GO.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-GO.pmtiles) | 184,8 MB | [carcara-GO-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-GO-leve.pmtiles) | 50,9 MB |
| Maranhão (MA) | [carcara-MA.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MA.pmtiles) | 113,1 MB | [carcara-MA-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MA-leve.pmtiles) | 28,2 MB |
| Mato Grosso (MT) | [carcara-MT.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MT.pmtiles) | 232,2 MB | [carcara-MT-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MT-leve.pmtiles) | 59,3 MB |
| Mato Grosso do Sul (MS) | [carcara-MS.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MS.pmtiles) | 111,6 MB | [carcara-MS-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MS-leve.pmtiles) | 29,6 MB |
| Minas Gerais (MG) | [carcara-MG.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MG.pmtiles) | 595,3 MB | [carcara-MG-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-MG-leve.pmtiles) | 183,3 MB |
| Pará (PA) | [carcara-PA.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PA.pmtiles) | 206,8 MB | [carcara-PA-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PA-leve.pmtiles) | 56,2 MB |
| Paraíba (PB) | [carcara-PB.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PB.pmtiles) | 75,9 MB | [carcara-PB-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PB-leve.pmtiles) | 21,2 MB |
| Paraná (PR) | [carcara-PR.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PR.pmtiles) | 330,2 MB | [carcara-PR-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PR-leve.pmtiles) | 100,3 MB |
| Pernambuco (PE) | [carcara-PE.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PE.pmtiles) | 105,6 MB | [carcara-PE-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PE-leve.pmtiles) | 26,4 MB |
| Piauí (PI) | [carcara-PI.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PI.pmtiles) | 115,7 MB | [carcara-PI-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-PI-leve.pmtiles) | 25,3 MB |
| Rio de Janeiro (RJ) | [carcara-RJ.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RJ.pmtiles) | 116,3 MB | [carcara-RJ-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RJ-leve.pmtiles) | 31,9 MB |
| Rio Grande do Norte (RN) | [carcara-RN.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RN.pmtiles) | 43,8 MB | [carcara-RN-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RN-leve.pmtiles) | 12,3 MB |
| Rio Grande do Sul (RS) | [carcara-RS.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RS.pmtiles) | 284,5 MB | [carcara-RS-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RS-leve.pmtiles) | 68,8 MB |
| Rondônia (RO) | [carcara-RO.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RO.pmtiles) | 53,7 MB | [carcara-RO-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RO-leve.pmtiles) | 15,3 MB |
| Roraima (RR) | [carcara-RR.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RR.pmtiles) | 39,0 MB | [carcara-RR-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-RR-leve.pmtiles) | 11,8 MB |
| Santa Catarina (SC) | [carcara-SC.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SC.pmtiles) | 228,8 MB | [carcara-SC-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SC-leve.pmtiles) | 57,9 MB |
| São Paulo (SP) | [carcara-SP.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SP.pmtiles) | 497,0 MB | [carcara-SP-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SP-leve.pmtiles) | 126,5 MB |
| Sergipe (SE) | [carcara-SE.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SE.pmtiles) | 29,6 MB | [carcara-SE-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-SE-leve.pmtiles) | 7,9 MB |
| Tocantins (TO) | [carcara-TO.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-TO.pmtiles) | 68,8 MB | [carcara-TO-leve.pmtiles](https://github.com/murkiriel/carcara/releases/download/2026-11-09-486b0133/carcara-TO-leve.pmtiles) | 17,2 MB |
<!-- downloads:end -->

### Usar

1. Leia o `catalogo.json` e escolha os pacotes pelo `bbox`: os estados por onde vai passar, a base para o resto do
   país, e os recursos.
2. Confira que a versão maior de `tileset.version` é uma que os seus estilos conhecem (hoje, a 4).
3. Baixe cada arquivo de `release_url` + `file` e confira o `sha256`. Use sempre o `release_url` do catálogo, não um
   link fixo de release.
4. Use o `.pmtiles` como veio, sem extrair nada. No MapLibre (Android desde a versão 11.7.0, e na web com a
   biblioteca `pmtiles`), basta prefixar o endereço da fonte:

   ```json
   { "sources": { "mapa": { "type": "vector", "url": "pmtiles://file:///caminho/para/carcara-GO.pmtiles" } } }
   ```

5. Mostre o crédito do campo `attribution`.

Mais de um estado ao mesmo tempo (um servidor local é o caminho recomendado), zooms, estilos, ícones e fontes:
[`docs/CONSUMO.md`](docs/CONSUMO.md).

## Formato

| Pacote | Conteúdo | Zoom |
|---|---|---|
| `carcara-base.pmtiles` | O Brasil inteiro em zoom baixo, para onde não há estado instalado | 0 a 9 |
| `carcara-<UF>.pmtiles` | Um por estado e o DF: todos os tiles que tocam o polígono da UF no IBGE, com ~5 km de margem; funciona sozinho | 0 a 15 |
| `carcara-<UF>-leve.pmtiles` | O mesmo estado sem os zooms 14 e 15 (cerca de 27% do tamanho do completo) | 0 a 13 |
| `carcara-recursos.tar.gz` | Ícones (`sprites/v4/`) e fontes (`fonts/`) da mesma versão do esquema, no formato que o MapLibre procura | — |

Os tiles são MVT compactados com gzip, no esquema do basemap da Protomaps, versão 4 (nove camadas: `earth`,
`landcover`, `landuse`, `water`, `buildings`, `boundaries`, `roads`, `places` e `pois`). Servem os estilos prontos
da Protomaps (`@protomaps/basemaps` 4.x) e qualquer estilo escrito contra essas camadas.

O `catalogo.json` (`"schema": 1`) traz a geração (`build_id`, `built_at`, `generator_commit`), o esquema dos tiles
(`tileset.version`), a origem (`source`, com o b3sum do build), o `release_url`, a `attribution` e, para a base, cada
estado e os recursos, o `file`, os `bytes` e o `sha256`. Todas as chaves estão em
[`docs/ARQUITETURA.md`](docs/ARQUITETURA.md#catalogojson).

**Coordenadas e ordem do `bbox`.** O `bbox` e o `bbox_tiles` de cada pacote vêm em graus decimais no WGS84
(EPSG:4326), com a **latitude primeiro**: `[lat_min, lon_min, lat_max, lon_max]` (no DF,
`[-16.05, -48.29, -15.5, -47.3]`). É o contrário do GeoJSON e do cabeçalho do PMTiles, que põem a longitude
primeiro: não passe o `bbox` direto para uma biblioteca de GeoJSON. A ordem fica assim no `schema` 1
([`docs/DECISOES.md`](docs/DECISOES.md), D13).

## Cobertura e limitações

- **O Brasil inteiro**: as 27 UFs, recortadas pela malha oficial do IBGE, e a base com o país até o zoom 9. O tile
  de divisa vem inteiro nos dois pacotes vizinhos.
- **Nada acima do zoom 15**: quem desenha amplia o tile do 15. Com o pacote leve, o detalhe de rua para no zoom 13.
- **Só o que a Protomaps publica.** Os pacotes não acrescentam nada ao esquema: não há atributo de superfície da via
  (pavimentada ou não), e a documentação cita camadas (`transit`, `physical_point`) que não aparecem nos tiles desta
  versão.
- **Recursos incompletos na origem:** só as fontes Noto Sans Regular, Medium e Italic (um estilo que peça outra fica
  sem rótulos) e não há ícone de posto de combustível nem de prefeitura (`townhall`).
- **Os dados são os do OpenStreetMap do dia do build**, com as lacunas e os erros dele.
- **Um pacote por estado, não por cidade**: o menor completo (AP) tem 24 MB; o maior (MG), 595 MB.

## Geração e reprodutibilidade

| Item | Como é |
|---|---|
| Gerador | Python, em [`gerador/`](gerador/README.md): recorta o build da Protomaps por estado, passa a geração pelas nove travas de validação, monta o catálogo e publica ([`docs/GERACAO.md`](docs/GERACAO.md)) |
| Origem dos tiles | Só o recorte do build da Protomaps (etapa A; a geração própria, etapa B, não está planejada: [`docs/DECISOES.md`](docs/DECISOES.md), D6) |
| Cadência | Uma geração nova toda semana, no domingo, pelo GitHub Actions (disparos às 03:17 e 09:17 de Brasília); se o domingo falhar, os dias seguintes tentam de novo |
| Se a geração falhar | A geração publicada continua no ar e fica aberta uma [issue](https://github.com/Murkiriel/carcara/issues) "Geração falhando" até a próxima dar certo |
| Gerações guardadas | As 12 mais recentes, como releases; as anteriores são apagadas, e os links delas deixam de funcionar |

**Só a geração corrente é reproduzível.** Refazer uma geração exige o mesmo build da Protomaps, que guarda os builds
por cerca de 7 dias; o projeto não os arquiva. Ficam registrados, para conferir: o b3sum e o endereço do build
(`source` do catálogo), o `generator_commit` e o sha256 de cada pacote. O resto é fixo no repositório: o Python 3.12,
as dependências travadas com hash (`gerador/requirements.in` → `gerador/requirements.txt`, instaladas com
`pip install --require-hashes`), as actions fixadas pelo SHA do commit, a ferramenta `pmtiles` com o sha256 conferido,
a malha do IBGE versionada e a imagem `ubuntu-24.04`. Com o mesmo build, o recorte sai idêntico byte a byte
([`docs/GERACAO.md`](docs/GERACAO.md#reprodutibilidade)).

## Licença e atribuição

Os **pacotes** são uma base derivada do OpenStreetMap, distribuída sob a **Open Database License (ODbL) 1.0** (texto
em [`LICENSE`](LICENSE)). Os tiles vêm do build da Protomaps, que também é ODbL.

- Cite "© colaboradores do OpenStreetMap".
- Se você publicar uma base derivada destes pacotes, ela precisa manter a ODbL.
- A camada `landcover` (zooms 0 a 7) é derivada do ESA WorldCover, sob **CC BY 4.0**: cite "© ESA WorldCover project
  2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium".
- Pacote de recursos: fontes Noto Sans sob a SIL Open Font License; ícones derivados de um conjunto MIT.
- Recorte por estado: malha das UFs do IBGE.

O texto completo do crédito está no `attribution` do `catalogo.json`, e cada release leva também um
`LICENCA-DADOS.txt`, com a licença e a atribuição. Detalhes em
[`docs/ARQUITETURA.md`](docs/ARQUITETURA.md#licenças-e-crédito).

O **código** (pasta `gerador/`) é **MIT** ([`gerador/LICENSE`](gerador/LICENSE)).

## Por que existe

Quem quer o mapa do Brasil offline tem hoje duas saídas, e as duas são ruins:

- **Baixar tile a tile do build público da Protomaps.** O arquivo mundial tem 138 GB e é lido por faixas de
  bytes, um pedido por tile. O retângulo de Goiás tem 602.806 tiles do zoom 8 ao 15; na prática, um estado inteiro
  só é viável até o zoom 13 (37.996 tiles), e o detalhe de rua fica restrito ao corredor de uma rota. A própria
  Protomaps pede para não usar esse endereço como infraestrutura: "copie o tileset para o seu armazenamento".
- **Gerar por conta própria.** Exige montar a geração, ter máquina e repetir a cada atualização.

Com um arquivo por estado, baixar Goiás vira **um download**, com o detalhe completo no estado inteiro, que pode
ser conferido por sha256, retomado, atualizado e apagado como um arquivo só.

| Tile a tile | Com os pacotes |
|---|---|
| Centenas de milhares de pedidos por estado | Um arquivo por estado |
| Estado inteiro só até o zoom 13 | Zoom 15 no estado inteiro |
| Depende de um endereço público sem garantia | Arquivo de release, com sha256 |
| Ícones e fontes vêm de outro servidor, no primeiro uso | Pacote de recursos da mesma geração |
| Centenas de milhares de arquivos pequenos no aparelho | Um arquivo, lido no lugar |

## Documentos

| Documento | O que tem |
|---|---|
| [`docs/DECISOES.md`](docs/DECISOES.md) | O que foi decidido, o que é só proposta, e as alternativas descartadas |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | Pacotes, zooms, recorte por estado, `catalogo.json`, releases, estrutura do repositório, licenças |
| [`docs/GERACAO.md`](docs/GERACAO.md) | Como os pacotes são gerados (o recorte do build da Protomaps), validação, agendamento, publicação e reprodutibilidade |
| [`docs/CONSUMO.md`](docs/CONSUMO.md) | Como um aplicativo ou site lê os pacotes |
| [`gerador/FONTES.md`](gerador/FONTES.md) | Fontes externas: o que foi conferido, quando e onde |
| [`gerador/PENDENCIAS.md`](gerador/PENDENCIAS.md) | Medições que faltam, decisões em aberto e riscos |

## Convenções

A regra em uma frase: **arquivos e pastas de dados em português; código e formato de dados em inglês; tudo o que
é texto para pessoas em português.**

| O quê | Idioma | Exemplos |
|---|---|---|
| Arquivos e pastas de dados e documentos | português, sem acento nem espaço | `catalogo.json`, `carcara-GO.pmtiles`, `carcara-recursos.tar.gz`, `PENDENCIAS.md`, `gerar.yml` |
| Código: variáveis, funções, classes, módulos, arquivos de código | inglês | `regions.py`, `measure.py`, `latest_build` |
| Opções de linha de comando | inglês | `--areas`, `--zooms`, `--dest` |
| Formato dos dados: chaves e valores do catálogo | inglês | `build_id`, `tileset_version`, `bbox` |
| Identificadores de automação (variáveis e jobs de workflow) | inglês | `CARCARA_PMTILES`, job `tests` |
| Comentários, docstrings, documentação, logs, erros | português | |
| Commits, releases, nomes dos passos de workflow | português | |
| Siglas e nomes próprios | como são | `ibge`, `osm`, `pmtiles` |

Nomes que o ecossistema espera ficam como são: `README.md`, `LICENSE`, `requirements.in`, `requirements.txt`, e, dentro do pacote de
recursos, as pastas `fonts/` e `sprites/` no formato que o MapLibre procura.

Todo formato publicado tem um campo de versão (`"schema": 1`), que só sobe quando um leitor antigo quebraria.
Datas em `AAAA-MM-DD`; horários do catálogo em UTC.

## Regras do repositório

- O repositório é independente e anônimo: **não cita nenhum aplicativo específico que use os pacotes**, não tem
  dados pessoais, e-mail pessoal nem caminhos de máquina local. Commits usam o e-mail anônimo do GitHub
  (`…@users.noreply.github.com`).
- Os arquivos gerados (`gerador/data/`) ficam fora do git: os pacotes vão para as releases.
- Código e dados em commits separados.
- Nasceu privado e ficou público em 2026-10-05, depois da revisão de abertura.

## Projetos irmãos

Quatro geradores independentes de dados abertos do Brasil para uso offline, um pacote por UF:

- **Carcará** (este): o mapa base, em PMTiles.
- [**Andorinha**](https://github.com/Murkiriel/andorinha): as rotas, em tiles do Valhalla.
- [**Sabiá**](https://github.com/Murkiriel/sabia): a busca de lugares e endereços, em SQLite.
- [**Pardal**](https://github.com/Murkiriel/pardal): os radares e os limites de velocidade, em CSV, GeoJSON, KML, GPX
  e SQLite.

Os quatro dividem o país nas mesmas 27 UFs, pelos limites do IBGE, e publicam um `catalogo.json` com o `sha256` de
cada arquivo e o `bbox` de cada UF em `[lat_min, lon_min, lat_max, lon_max]`, no WGS84. Carcará, Andorinha e Sabiá
seguem o mesmo molde de catálogo e de release (`schema` 1, `build_id` como etiqueta da release, `release_url`,
`base` e `states`) e dão o mesmo `bbox` para cada UF; o catálogo do Pardal tem formato próprio (`ufs`).

## English

**Carcará** publishes an **offline vector basemap of Brazil** as [PMTiles](https://docs.protomaps.com/pmtiles/) in the
Protomaps basemap schema (v4): a base pack (the whole country up to zoom 9), one pack per state (up to zoom 15, plus a
light version up to zoom 13) and a resources pack (sprites and fonts). The packs are cut every week, on Sunday, from
the daily Protomaps build of OpenStreetMap and published as GitHub release assets, indexed by
[`catalogo.json`](catalogo.json) (sizes, sha256 and a `bbox` per pack, WGS84, latitude first:
`[lat_min, lon_min, lat_max, lon_max]`, unlike GeoJSON). MapLibre reads the files directly with the `pmtiles://`
prefix. Only the current generation is reproducible: dependencies are locked with hashes and actions pinned by commit
SHA, but Protomaps keeps its builds for about 7 days. Data under the ODbL 1.0 (© OpenStreetMap contributors; land
cover © ESA WorldCover, CC BY 4.0); generator code under MIT. Sister projects: routing
([Andorinha](https://github.com/Murkiriel/andorinha)), search ([Sabiá](https://github.com/Murkiriel/sabia)) and speed
cameras and limits ([Pardal](https://github.com/Murkiriel/pardal)).

<sub>Palavras-chave: mapa offline Brasil, mapa base vetorial, PMTiles Brasil, tiles vetoriais, Protomaps,
OpenStreetMap Brasil, MapLibre offline, mapa por estado, mapa sem internet.</sub>
