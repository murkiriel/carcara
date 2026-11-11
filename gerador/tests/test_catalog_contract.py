"""O bloco `contract` do catalogo.json: o contrato de catálogo comum v1 (docs/CATALOGO.md).

Confere o formato contra o esquema (docs/catalogo-v1.schema.json), as regras que o esquema não expressa, as URLs
absolutas, os sha256 iguais aos das chaves antigas, a ordem do bbox e o bloco do esquema de tiles amarrado ao config.
"""
import copy
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

GENERATOR_DIR = Path(__file__).resolve().parent.parent
REPO = GENERATOR_DIR.parent
sys.path.insert(0, str(GENERATOR_DIR))
from carcara import catalog, config, resources  # noqa: E402
from tests import contract_check  # noqa: E402
from tests.test_catalog import BUILD, POLYGONS, RESOURCES, generation  # noqa: E402

DOCS = REPO / "docs"
FULL = "0123456789abcdef0123456789abcdef01234567"


def built(light=True, **kwargs):
    kwargs.setdefault("generator_commit", FULL[:7])
    kwargs.setdefault("generator_commit_full", FULL)
    return catalog.build_catalog(BUILD, generation(light), RESOURCES, POLYGONS, osm_timestamp="2026-10-01T04:00:00Z",
                                 built_at="2026-10-01T17:30:00Z", **kwargs)


class ContractTestCase(unittest.TestCase):
    def setUp(self):
        self.cat = built()
        self.block = self.cat["contract"]
        self.files = {f["id"]: f for f in self.block["files"]}

    def legacy(self, file_id):
        if file_id == "base":
            return self.cat["base"]
        if file_id == "recursos":
            return self.cat["resources"]
        if file_id.endswith("-leve"):
            return self.cat["states"][file_id[:2]]["light"]
        return self.cat["states"][file_id]


class ContractShapeTest(ContractTestCase):
    def test_valid_against_the_schema_and_the_rules(self):
        self.assertEqual([], contract_check.problems(self.cat, DOCS))
        self.assertEqual([], contract_check.problems(built(light=False), DOCS))

    def test_the_checker_catches_a_broken_block(self):
        broken = copy.deepcopy(self.cat)
        broken["contract"]["files"][0]["url"] = "carcara-base.pmtiles"  # relativa
        self.assertTrue(contract_check.problems(broken, DOCS))

    def test_identity_and_versions(self):
        b = self.block
        self.assertEqual(("catalogo-comum", 1, 1, "carcara"), (b["name"], b["version"], b["min_reader_version"],
                                                               b["dataset"]))
        self.assertEqual((self.cat["build_id"], self.cat["built_at"], self.cat["release_url"]),
                         (b["build_id"], b["built_at"], b["release_url"]))
        self.assertEqual({"crs": "EPSG:4326", "bbox_order": "lat_min,lon_min,lat_max,lon_max"}, b["coordinates"])

    def test_generator_full_commit_and_licences(self):
        self.assertEqual({"repository": config.REPOSITORY_URL, "commit": FULL}, self.block["generator"])
        self.assertEqual(FULL[:7], self.cat["generator_commit"])
        self.assertEqual({"data": "ODbL-1.0", "code": "MIT", "attribution": config.ATTRIBUTION}, self.block["license"])
        self.assertEqual("OFL-1.1 AND MIT", self.files["recursos"]["license"])

    def test_a_commit_that_is_not_the_catalog_one_is_refused(self):
        with self.assertRaises(ValueError):
            built(generator_commit="abc1234", generator_commit_full=FULL)

    def test_full_commit_from_the_checkout(self):
        sha = catalog.git_commit_full()
        self.assertTrue(sha is None or re.fullmatch(r"[0-9a-f]{40}", sha), sha)

    def test_sources_with_dates_and_checksums(self):
        sources = {s["id"]: s for s in self.block["sources"]}
        build = sources["protomaps-build"]
        self.assertEqual((BUILD["url"], BUILD["uploaded"], {"b3sum": BUILD["b3sum"]}),
                         (build["url"], build["date"], build["checksums"]))
        self.assertEqual({"sha256": config.IBGE_MESH_COPY_SHA256}, sources["ibge-malha-uf"]["checksums"])
        assets = sources["protomaps-basemaps-assets"]
        self.assertEqual((config.ASSETS_REVISION, {"sha256": config.ASSETS_CONTENT_SHA256}),
                         (assets["version"], assets["checksums"]))
        self.assertEqual({"date": "2026-10-01T04:00:00Z", "md5": None}, self.block["osm_snapshot"])


class ContractFilesTest(ContractTestCase):
    def test_every_published_file_once(self):
        self.assertEqual({"base", "DF", "DF-leve", "GO", "GO-leve", "recursos"}, set(self.files))
        without_light = {f["id"] for f in built(light=False)["contract"]["files"]}
        self.assertEqual({"base", "DF", "GO", "recursos"}, without_light)

    def test_absolute_urls_are_release_url_plus_file(self):
        for file_id, f in self.files.items():
            self.assertTrue(f["url"].startswith("https://"), f["url"])
            self.assertEqual(self.cat["release_url"] + self.legacy(file_id)["file"], f["url"])

    def test_sha256_and_sizes_are_the_legacy_ones(self):
        for file_id, f in self.files.items():
            old = self.legacy(file_id)
            self.assertEqual((old["sha256"], old["bytes"]), (f["sha256"], f["bytes"]), file_id)
            if f["format"] == "pmtiles":
                self.assertEqual((old["minzoom"], old["maxzoom"], old["tiles"]),
                                 (f["minzoom"], f["maxzoom"], f["tiles"]), file_id)

    def test_bbox_is_the_area_served_latitude_first(self):
        self.assertEqual(self.cat["base"]["bbox"], self.files["base"]["bbox"])
        for state in ("DF", "GO"):
            self.assertEqual(self.cat["states"][state]["bbox"], self.files[state]["bbox"])
            self.assertEqual(self.cat["states"][state]["bbox"], self.files[state + "-leve"]["bbox"])
        self.assertEqual([-19.5, -53.25, -12.39, -45.9], self.files["GO"]["bbox"])
        self.assertIsNone(self.files["recursos"]["bbox"])

    def test_kinds_levels_and_dependencies(self):
        expected = {"base": ("base", "BR", "BASE_HIGHWAYS_ONLY", ["recursos"]),
                    "GO": ("uf", "GO", "DETAILED", ["recursos"]),
                    "GO-leve": ("uf_light", "GO", "DETAILED", ["recursos"]),
                    "recursos": ("resources", None, None, [])}
        for file_id, values in expected.items():
            f = self.files[file_id]
            self.assertEqual(values, (f["kind"], f["region"], f["coverage_level"], f["requires"]), file_id)

    def test_zoom_ranges(self):
        self.assertEqual((0, config.BASE_MAX_ZOOM), (self.files["base"]["minzoom"], self.files["base"]["maxzoom"]))
        self.assertEqual((0, config.MAX_ZOOM), (self.files["GO"]["minzoom"], self.files["GO"]["maxzoom"]))
        self.assertEqual((0, config.LIGHT_MAX_ZOOM), (self.files["GO-leve"]["minzoom"], self.files["GO-leve"]["maxzoom"]))

    def test_formats_and_unpacking(self):
        for f in self.files.values():
            if f["kind"] == "resources":
                self.assertEqual(("glyphs-sprites", "application/gzip", ["gzip", "tar"]),
                                 (f["format"], f["media_type"], f["unpack"]))
            else:
                self.assertEqual(("pmtiles", "application/vnd.pmtiles", [], None),
                                 (f["format"], f["media_type"], f["unpack"], f["bytes_unpacked"]))


class TilesetCompatibilityTest(ContractTestCase):
    def test_block_equals_the_config_and_the_legacy_keys(self):
        compat = self.block["compatibility"]
        carcara = compat["carcara"]
        self.assertTrue(compat["mix_generations"])
        self.assertEqual({"name": "pmtiles", "version": "3"}, compat["data_format"])
        self.assertEqual({"name": "protomaps-basemap", "version": BUILD["version"], "major": config.TILESET_MAJOR_VERSION},
                         carcara["tileset"])
        self.assertEqual(self.cat["tileset"]["version"], carcara["tileset"]["version"])
        self.assertEqual((config.PMTILES_SPEC_VERSION, self.cat["tile_format"], self.cat["tile_compression"]),
                         (carcara["pmtiles_version"], carcara["tile_type"], carcara["tile_compression"]))

    def test_glyphs_and_sprites_are_where_the_resources_put_them(self):
        carcara = self.block["compatibility"]["carcara"]
        self.assertEqual(list(resources.FONTSTACKS), carcara["glyphs"]["fontstacks"])
        self.assertEqual(list(resources.SPRITE_FLAVORS), carcara["sprites"]["flavors"])
        names = set(resources.required())
        stack, flavor = resources.FONTSTACKS[0], resources.SPRITE_FLAVORS[0]
        glyph = carcara["glyphs"]["template"].format(fontstack=stack, range="0-255")
        self.assertIn(glyph, names)
        sprite = carcara["sprites"]["template"].format(flavor=flavor)
        self.assertTrue({sprite + ".json", sprite + ".png"} <= names, sprite)

    def test_the_files_are_pmtiles_of_the_declared_version(self):
        header = (GENERATOR_DIR / "tests" / "fixtures" / "bairro.pmtiles").read_bytes()[:8]
        self.assertEqual(b"PMTiles", header[:7])
        self.assertEqual(config.PMTILES_SPEC_VERSION, header[7])

    def test_a_catalog_of_another_major_version_is_refused(self):
        cat = built()
        cat["tileset"]["version"] = "5.0.0"
        with self.assertRaises(ValueError):
            catalog.contract(cat, FULL)


class OnlyAddsTest(ContractTestCase):
    def test_the_old_keys_are_untouched(self):
        self.assertEqual(["schema", "build_id", "built_at", "generator_commit", "tileset", "source", "tile_format",
                          "tile_compression", "release_url", "attribution", "resources", "base", "states", "contract"],
                         list(self.cat))
        self.assertEqual(1, self.cat["schema"])


class SharedDocumentsTest(unittest.TestCase):
    def test_spec_and_schema_are_the_shared_ones(self):
        self.assertEqual({}, contract_check.doc_mismatches(DOCS))

    def test_the_readme_points_to_the_spec(self):
        self.assertIn("docs/CATALOGO.md", (REPO / "README.md").read_text(encoding="utf-8"))


class RecatalogTest(unittest.TestCase):
    """scripts/recatalog.py sobre o catálogo publicado na raiz: só acrescenta `contract`."""

    def setUp(self):
        sys.path.insert(0, str(GENERATOR_DIR / "scripts"))

    def test_rebuilds_the_published_catalog(self):
        published = json.loads((REPO / "catalogo.json").read_text(encoding="utf-8"))
        if catalog.git_commit_full(published["generator_commit"]) is None:
            self.skipTest("o commit da geração publicada não está neste checkout (clone raso)")
        import recatalog  # noqa: E402
        out = recatalog.rebuild(published)
        self.assertEqual({k: v for k, v in published.items() if k != "contract"},
                         {k: v for k, v in out.items() if k != "contract"})
        self.assertEqual([], contract_check.problems(out, DOCS))
        lights = sum(1 for entry in published["states"].values() if entry.get("light"))
        self.assertEqual(len(published["states"]) + lights + 2, len(out["contract"]["files"]))

    def test_constants_are_read_without_running_the_file(self):
        import recatalog  # noqa: E402
        head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
        if head.returncode != 0:
            self.skipTest("sem git")
        found = recatalog.constants_at(head.stdout.strip(), ["ASSETS_REVISION", "NAO_EXISTE"])
        self.assertEqual({"ASSETS_REVISION": config.ASSETS_REVISION}, found)


if __name__ == "__main__":
    unittest.main()
