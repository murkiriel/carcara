"""Os estilos prontos: o que está no repositório, a conferência contra o pacote de recursos e a folha do Carcará."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from carcara import config, png, resources, styles, validation  # noqa: E402

ESTILOS = config.GENERATOR_DIR / "estilos"
NAME = ["coalesce", ["get", "name:pt"], ["get", "name"]]


def load(flavor: str) -> dict:
    return json.loads((styles.STYLES_DIR / f"{flavor}.json").read_text(encoding="utf-8"))


def index(names, ratio: int = 1) -> bytes:
    return json.dumps({name: {"x": 0, "y": 0, "width": 4, "height": 4, "pixelRatio": ratio} for name in names}).encode()


def pack_files() -> dict:
    """Um pacote de recursos do jeito que a geração monta, só com o que a conferência dos estilos lê."""
    files = {f"fonts/{stack}/{glyph_range}.pbf": b"" for stack in resources.FONTSTACKS
             for glyph_range in ("0-255", "256-511")}
    for flavor in resources.SPRITE_FLAVORS:
        for density in styles.DENSITIES:
            files[f"{styles.UPSTREAM_SPRITES_FOLDER}{flavor}{density}.json"] = index(validation.required_icons(flavor))
            files[f"{styles.UPSTREAM_SPRITES_FOLDER}{flavor}{density}.png"] = b""
    for flavor in styles.OWN_SPRITE_FLAVORS:
        for density in styles.DENSITIES:
            icons = [*validation.required_icons(flavor), *styles.OWN_ICONS]
            files[f"{styles.OWN_SPRITES_FOLDER}{flavor}{density}.json"] = index(icons)
            files[f"{styles.OWN_SPRITES_FOLDER}{flavor}{density}.png"] = b""
    return files


def walk(value):
    yield value
    if isinstance(value, list):
        for part in value:
            yield from walk(part)
    elif isinstance(value, dict):
        for part in value.values():
            yield from walk(part)


class CommittedStylesTest(unittest.TestCase):
    """Os estilos de estilos/gerado/, como vão para o pacote."""

    def test_every_flavour_is_there_and_passes_the_check(self):
        files = pack_files()
        for name, data in styles.committed().items():
            self.assertEqual([], styles.problems(name, data, files), name)

    def test_at_least_light_and_dark(self):
        self.assertEqual(("light", "dark"), styles.FLAVORS[:2])
        self.assertEqual("Carcará claro", load("light")["name"])
        self.assertEqual("Carcará escuro", load("dark")["name"])

    def test_only_layers_of_the_schema(self):
        for flavor in styles.FLAVORS:
            used = {layer["source-layer"] for layer in load(flavor)["layers"] if "source-layer" in layer}
            self.assertLessEqual(used, set(styles.SCHEMA_LAYERS), flavor)
            self.assertNotIn("transit", used)
            self.assertNotIn("physical_point", used)

    def test_schema_layers_are_the_ones_the_consumption_guide_lists(self):
        text = (config.REPO / "docs" / "CONSUMO.md").read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if "têm nove camadas" in line)
        following = text[text.index(line):text.index(line) + 400]
        for layer in styles.SCHEMA_LAYERS:
            self.assertIn(f"`{layer}`", following)

    def test_only_the_three_fonts_of_the_pack(self):
        for flavor in styles.FLAVORS:
            text = (styles.STYLES_DIR / f"{flavor}.json").read_text(encoding="utf-8")
            self.assertEqual(set(resources.FONTSTACKS), set(re.findall(r'"(Noto Sans [^"]*)"', text)), flavor)
            self.assertNotIn("Devanagari", text)

    def test_labels_in_portuguese_with_the_local_name_as_fallback(self):
        for flavor in styles.FLAVORS:
            for layer in load(flavor)["layers"]:
                field = (layer.get("layout") or {}).get("text-field")
                if field is None:
                    continue
                names = {part[1] for part in walk(field)
                         if isinstance(part, list) and len(part) == 2 and part[0] == "get"}
                if any(name.startswith("name") for name in names):
                    self.assertIn(NAME, list(walk(field)), layer["id"])
                    self.assertLessEqual(names - {"ref", "ref:en"}, {"name:pt", "name"}, layer["id"])

    def test_addresses_are_templates_for_the_app(self):
        for flavor in styles.FLAVORS:
            style = load(flavor)
            self.assertEqual("{recursos}/fonts/{fontstack}/{range}.pbf", style["glyphs"])
            folder = "carcara-v4" if flavor in styles.OWN_SPRITE_FLAVORS else "v4"
            self.assertEqual(f"{{recursos}}/sprites/{folder}/{flavor}", style["sprite"])
            self.assertEqual({"carcara"}, set(style["sources"]))
            self.assertEqual("{tiles}", style["sources"]["carcara"]["url"])
            self.assertEqual(config.EMBEDDED_ATTRIBUTION, style["sources"]["carcara"]["attribution"])
            text = json.dumps({key: value for key, value in style.items() if key != "sources"})
            self.assertNotRegex(text, r"https?://", flavor)  # nenhum endereço fixo fora do crédito

    def test_buildings_in_3d_from_zoom_14_with_a_default_height(self):
        for flavor in styles.FLAVORS:
            style = load(flavor)
            layers = style["layers"]
            ids = [layer["id"] for layer in layers]
            extrusion = layers[ids.index("buildings_3d")]
            self.assertEqual("fill-extrusion", extrusion["type"])
            self.assertEqual("buildings", extrusion["source-layer"])
            self.assertEqual(14, extrusion["minzoom"])
            paint = json.dumps(extrusion["paint"])
            self.assertIn('["coalesce", ["get", "height"], 5]', paint)
            self.assertIn('["coalesce", ["get", "min_height"], 0]', paint)
            self.assertEqual(5, style["metadata"]["carcara:altura_padrao_predios"])
            # Acima de vias e limites, abaixo de todo rótulo; a planta plana some no zoom em que o 3D aparece.
            first_symbol = next(i for i, layer in enumerate(layers) if layer["type"] == "symbol")
            self.assertEqual(first_symbol - 1, ids.index("buildings_3d"))
            self.assertEqual(15, layers[ids.index("buildings")]["maxzoom"])

    def test_poi_icons_are_spelled_out_and_include_the_own_ones(self):
        for flavor in styles.OWN_SPRITE_FLAVORS:
            pois = next(layer for layer in load(flavor)["layers"] if layer["id"] == "pois")
            icon = pois["layout"]["icon-image"]
            self.assertEqual(["match", ["get", "kind"]], icon[:2])
            outputs = dict(zip(icon[2:-1:2], icon[3:-1:2]))
            self.assertEqual("fuel", outputs["fuel"])
            self.assertEqual("townhall", outputs["townhall"])
            self.assertEqual("train_station", outputs["station"])
            self.assertIn("fuel", json.dumps(pois["filter"]))

    def test_plain_flavours_have_no_points_of_interest(self):
        for flavor in set(styles.FLAVORS) - set(styles.OWN_SPRITE_FLAVORS):
            self.assertNotIn("pois", [layer["id"] for layer in load(flavor)["layers"]])

    def test_generated_by_the_pinned_package(self):
        package = json.loads((ESTILOS / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((ESTILOS / "package-lock.json").read_text(encoding="utf-8"))
        for name, version in package["dependencies"].items():
            self.assertRegex(version, r"^\d+\.\d+\.\d+$", name)  # versão exata, sem ^ nem ~
            locked = lock["packages"][f"node_modules/{name}"]
            self.assertEqual(version, locked["version"], name)
            self.assertRegex(locked["integrity"], r"^sha512-", name)
        self.assertTrue(all(entry.get("integrity", "").startswith("sha512-")
                            for key, entry in lock["packages"].items() if key))
        version = package["dependencies"]["@protomaps/basemaps"]
        for flavor in styles.FLAVORS:
            self.assertEqual(f"@protomaps/basemaps {version}", load(flavor)["metadata"]["carcara:origem"])

    def test_the_tests_workflow_checks_them_against_the_generator(self):
        text = (config.REPO / ".github" / "workflows" / "testes.yml").read_text(encoding="utf-8")
        self.assertIn("working-directory: gerador/estilos", text)
        self.assertIn("npm ci --ignore-scripts", text)
        self.assertIn("node gerar.mjs --conferir", text)

    def test_node_modules_stays_out_of_git(self):
        self.assertIn("gerador/estilos/node_modules/",
                      (config.REPO / ".gitignore").read_text(encoding="utf-8").splitlines())


class ProblemsTest(unittest.TestCase):
    """A conferência de um estilo contra o pacote: cada erro que ela tem de pegar."""

    def setUp(self):
        self.files = pack_files()
        self.style = load("light")

    def problems(self, style=None):
        data = json.dumps(style if style is not None else self.style).encode()
        return styles.problems("styles/light.json", data, self.files)

    def layer(self, layer_id):
        return next(layer for layer in self.style["layers"] if layer["id"] == layer_id)

    def assertOne(self, *fragments):
        found = self.problems()
        self.assertEqual(1, len(found), found)
        for fragment in fragments:
            self.assertIn(fragment, found[0])

    def test_good_style(self):
        self.assertEqual([], self.problems())

    def test_not_json(self):
        found = styles.problems("styles/light.json", b"{\"version\": 8", self.files)
        self.assertEqual(1, len(found))
        self.assertIn("JSON", found[0])

    def test_not_a_style(self):
        self.assertIn("version", self.problems({"layers": []})[0])

    def test_layer_of_another_schema(self):
        self.layer("roads_major")["source-layer"] = "transportation"
        self.assertOne("roads_major (transportation)")

    def test_layer_reading_another_source(self):
        self.layer("water")["source"] = "openmaptiles"
        self.assertOne("water", "openmaptiles")

    def test_font_the_pack_does_not_have(self):
        self.layer("places_locality")["layout"]["text-font"] = ["case", True, ["literal", ["Noto Sans Bold"]],
                                                                ["literal", ["Noto Sans Regular"]]]
        self.assertOne("Noto Sans Bold")

    def test_font_inside_a_format_expression(self):
        self.layer("places_country")["layout"]["text-field"] = [
            "format", ["get", "name"], {"text-font": ["literal", ["Noto Sans Devanagari Regular v1"]]}]
        self.assertOne("Noto Sans Devanagari Regular v1")

    def test_two_fonts_in_one_stack(self):
        self.layer("pois")["layout"]["text-font"] = ["Noto Sans Regular", "Noto Sans Medium"]
        self.assertOne("Noto Sans Regular, Noto Sans Medium")

    def test_icon_the_sheet_does_not_have(self):
        icon = self.layer("pois")["layout"]["icon-image"]
        icon[-1] = "hospital"
        self.assertOne("hospital", "hospital (2x)")

    def test_icon_that_depends_on_the_data_cannot_be_checked(self):
        self.layer("pois")["layout"]["icon-image"] = ["get", "kind"]
        self.assertOne("não dá para conferir", "icon-image de pois")

    def test_shield_icons_by_length(self):
        shields = self.layer("roads_shields")["layout"]["icon-image"]
        self.assertIn("generic_shield-5char", styles._outputs(shields))
        self.assertNotIn("generic_shield-6char", styles._outputs(shields))

    def test_sprite_sheet_without_the_own_icons(self):
        self.style["sprite"] = "{recursos}/sprites/v4/light"
        self.assertOne("fuel", "townhall")

    def test_sprite_sheet_missing_from_the_pack(self):
        self.style["sprite"] = "{recursos}/sprites/v5/light"
        found = self.problems()
        self.assertEqual(1, len(found), found)
        self.assertIn("sprites/v5/light", found[0])

    def test_fixed_addresses_are_refused(self):
        self.style["glyphs"] = "https://exemplo.invalid/fonts/{fontstack}/{range}.pbf"
        self.style["sprite"] = "https://exemplo.invalid/sprites/v4/light"
        self.style["sources"]["carcara"]["url"] = "pmtiles://https://exemplo.invalid/x.pmtiles"
        found = self.problems()
        self.assertEqual(3, len(found), found)

    def test_extra_source(self):
        self.style["sources"]["outra"] = copy.deepcopy(self.style["sources"]["carcara"])
        self.assertOne("outra")

    def test_repeated_layer_id(self):
        self.style["layers"].append(copy.deepcopy(self.layer("water")))
        self.assertOne("repetidas", "water")


class OwnSpritesTest(unittest.TestCase):
    def test_icons_go_in_a_new_row_below_the_sheet(self):
        sheet = png.Image(10, 6)
        sheet.pixels[:] = bytes((1, 2, 3, 255)) * 60
        icon_a, icon_b = png.Image(4, 4, bytes((9, 9, 9, 255)) * 16), png.Image(8, 3, bytes((7, 7, 7, 255)) * 24)
        image, entries = styles.compose(sheet, {"old": {"x": 0, "y": 0}}, [("a", icon_a), ("b", icon_b)], 2)
        # Folga de 1 pixel de 1x, isto é, 2 pixels nesta densidade.
        self.assertEqual({"x": 0, "y": 8, "width": 4, "height": 4, "pixelRatio": 2}, entries["a"])
        self.assertEqual({"x": 6, "y": 8, "width": 8, "height": 3, "pixelRatio": 2}, entries["b"])
        self.assertEqual({"x": 0, "y": 0}, entries["old"])
        self.assertEqual((14, 12), (image.width, image.height))
        self.assertEqual((1, 2, 3, 255), image.pixel(9, 5))
        self.assertEqual((9, 9, 9, 255), image.pixel(3, 11))
        self.assertEqual((7, 7, 7, 255), image.pixel(13, 10))
        self.assertEqual((0, 0, 0, 0), image.pixel(13, 6))  # a folga fica transparente

    def test_icon_the_upstream_sheet_already_has_is_refused(self):
        with self.assertRaises(RuntimeError) as ctx:
            styles.compose(png.Image(2, 2), {"townhall": {}}, [("townhall", png.Image(1, 1))], 1)
        self.assertIn("townhall", str(ctx.exception))

    def test_own_icons_are_drawn_in_every_flavour_and_density(self):
        for name in styles.OWN_ICONS:
            self.assertTrue((styles.STYLES_DIR.parent / "icones" / f"{name}.svg").is_file(), name)
            for flavor in styles.OWN_SPRITE_FLAVORS:
                for density, ratio in styles.DENSITIES.items():
                    icon = styles.own_icon(name, flavor, density)
                    self.assertEqual((19 * ratio, 19 * ratio), (icon.width, icon.height), (name, flavor, density))

    def test_composed_sheet_from_a_real_sheet(self):
        upstream = png.Image(30, 20, bytes((5, 6, 7, 255)) * 600)
        files = {}
        for flavor in styles.OWN_SPRITE_FLAVORS:
            for density in styles.DENSITIES:
                files[f"sprites/v4/{flavor}{density}.png"] = png.encode(upstream)
                files[f"sprites/v4/{flavor}{density}.json"] = index(["arrow"])
        found = styles.own_sprites(files)
        self.assertEqual(sorted(name for flavor in styles.OWN_SPRITE_FLAVORS
                                for name in styles.sprite_files("sprites/carcara-v4/", flavor)), sorted(found))
        entries = json.loads(found["sprites/carcara-v4/dark@2x.json"])
        image = png.decode(found["sprites/carcara-v4/dark@2x.png"])
        fuel = styles.own_icon("fuel", "dark", "@2x")
        self.assertEqual(2, entries["fuel"]["pixelRatio"])
        self.assertEqual(fuel.pixel(19, 19), image.pixel(entries["fuel"]["x"] + 19, entries["fuel"]["y"] + 19))
        self.assertEqual({"arrow", "fuel", "townhall"}, set(entries))


class PngTest(unittest.TestCase):
    def test_round_trip(self):
        image = png.Image(3, 2, bytes(range(24)))
        self.assertEqual(image.pixels, png.decode(png.encode(image)).pixels)

    def test_same_image_same_bytes(self):
        self.assertEqual(png.encode(png.Image(5, 5)), png.encode(png.Image(5, 5)))

    def test_palette_with_transparency(self):
        import struct
        import zlib

        def chunk(kind, body):
            return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
        data = (png.SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 3, 0, 0, 0))
                + chunk(b"PLTE", bytes((255, 0, 0, 0, 0, 255))) + chunk(b"tRNS", bytes((128,)))
                + chunk(b"IDAT", zlib.compress(bytes((0, 0, 1)))) + chunk(b"IEND", b""))
        image = png.decode(data)
        self.assertEqual((255, 0, 0, 128), image.pixel(0, 0))
        self.assertEqual((0, 0, 255, 255), image.pixel(1, 0))

    def test_not_a_png(self):
        with self.assertRaises(ValueError):
            png.decode(b"GIF89a")


if __name__ == "__main__":
    unittest.main()
