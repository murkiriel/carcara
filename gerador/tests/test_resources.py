import gzip
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from carcara import config, png, resources, styles  # noqa: E402
from tests.fake_server import FakeServer  # noqa: E402

REVISION = "0123456789abcdef0123456789abcdef01234567"
TOP = f"basemaps-assets-{REVISION}/"


def sheet(flavor: str, density: str) -> bytes:
    """Uma folha de ícones de verdade, pequena, com um pixel que diz de qual variação ela é."""
    image = png.Image(8, 4)
    image.pixels[0:4] = bytes((len(flavor), len(density), 7, 255))
    return png.encode(image)


def upstream_files(without=(), extra=None) -> dict:
    """O que o repositório de origem tem, no formato dele: fontes por faixa, folhas de ícones por versão, e o resto."""
    files = {"README.md": b"# basemaps-assets", "fonts.json": b"[]", ".github/FUNDING.yml": b"x",
             "scripts/create_fonts.sh": b"#!/bin/sh", "scripts/LICENSE.md": b"BSD", "fonts/OFL.txt": b"SIL OFL 1.1"}
    for stack in resources.FONTSTACKS:
        for glyph_range in resources.ranges():
            files[f"fonts/{stack}/{glyph_range}.pbf"] = f"{stack} {glyph_range}".encode()
    for flavor in resources.SPRITE_FLAVORS:
        for density in ("", "@2x"):
            files[f"sprites/v4/{flavor}{density}.json"] = b"{}"
            files[f"sprites/v4/{flavor}{density}.png"] = sheet(flavor, density)
            files[f"sprites/v3/{flavor}{density}.json"] = b"{}"
            files[f"sprites/v3/{flavor}{density}.png"] = b"antigo"
    for name in without:
        del files[name]
    files.update(extra or {})
    return files


def upstream_archive(files: dict, links=()) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(TOP + name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        for name, target in links:
            info = tarfile.TarInfo(TOP + name)
            info.type = tarfile.SYMTYPE
            info.linkname = target
            tar.addfile(info)
    return buffer.getvalue()


def members(archive: Path) -> dict:
    with tarfile.open(archive, "r:gz") as tar:
        return {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}


class RangesTest(unittest.TestCase):
    def test_256_ranges_of_256_code_points(self):
        names = list(resources.ranges())
        self.assertEqual(256, len(names))
        self.assertEqual("0-255", names[0])
        self.assertEqual("256-511", names[1])
        self.assertEqual("65280-65535", names[-1])


class PinnedRevisionTest(unittest.TestCase):
    def test_revision_and_content_are_pinned(self):
        self.assertRegex(config.ASSETS_REVISION, r"^[0-9a-f]{40}$")
        self.assertRegex(config.ASSETS_CONTENT_SHA256, r"^[0-9a-f]{64}$")
        self.assertIn("{revision}", config.ASSETS_ARCHIVE_URL)


class BuildTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dist = self.root / "dist"
        self.server = FakeServer().__enter__()
        self._patches = [mock.patch.object(config, "RAW", self.root / "raw"),
                         mock.patch.object(config, "ASSETS_REVISION", REVISION),
                         mock.patch.object(config, "ASSETS_ARCHIVE_URL", self.server.url("/{revision}.tar.gz")),
                         mock.patch.object(resources, "RETRY_DELAY", 0)]
        for p in self._patches:
            p.start()
        self.publish(upstream_files())

    def tearDown(self):
        mock.patch.stopall()
        self.server.__exit__(None, None, None)
        self._tmp.cleanup()

    def publish(self, files: dict, links=(), pin=True):
        """Põe o arquivo de origem no servidor. Com `pin`, o config passa a esperar exatamente este conteúdo."""
        self.server.files[f"/{REVISION}.tar.gz"] = upstream_archive(files, links)
        if pin:
            digest = resources.content_digest(resources.select(files))
            mock.patch.object(config, "ASSETS_CONTENT_SHA256", digest).start()

    def test_pack_has_every_font_range_the_sprites_and_the_licences(self):
        pack = resources.build(self.dist)
        self.assertEqual(self.dist / "carcara-recursos.tar.gz", pack["path"])
        inside = members(pack["path"])
        for stack in resources.FONTSTACKS:
            self.assertEqual(f"{stack} 0-255".encode(), inside[f"fonts/{stack}/0-255.pbf"])
            self.assertEqual(256, sum(1 for name in inside if name.startswith(f"fonts/{stack}/")))
        self.assertEqual(sheet("light", "@2x"), inside["sprites/v4/light@2x.png"])
        self.assertEqual(20, sum(1 for name in inside if name.startswith("sprites/v4/")))
        self.assertEqual(b"SIL OFL 1.1", inside["fonts/OFL.txt"])
        self.assertIn(b"MIT", inside["sprites/LICENCA.md"])
        self.assertIn("LEIAME.md", inside)

    def test_reports_what_was_packed(self):
        pack = resources.build(self.dist)
        self.assertEqual("carcara-recursos.tar.gz", pack["file"])
        self.assertEqual(pack["path"].stat().st_size, pack["bytes"])
        self.assertRegex(pack["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(REVISION, pack["revision"])
        self.assertEqual(3 * 256, pack["glyph_files"])
        self.assertEqual(20, pack["sprite_files"])

    def test_leaves_out_what_no_version_4_style_asks_for(self):
        inside = members(resources.build(self.dist)["path"])
        for name in inside:
            self.assertFalse(name.startswith(("sprites/v3/", "scripts/", ".github/")), name)
        self.assertNotIn("README.md", inside)
        self.assertNotIn("fonts.json", inside)

    def test_font_for_another_script_is_left_out_whole(self):
        # Na origem, a pasta dessa fonte tem quatro arquivos de verdade e o resto são links para a fonte comum.
        other = "Noto Sans Devanagari Regular v1"
        files = upstream_files(extra={f"fonts/{other}/62720-62975.pbf": b"de verdade"})
        self.publish(files, links=[(f"fonts/{other}/0-255.pbf", "../Noto Sans Regular/0-255.pbf")])
        inside = members(resources.build(self.dist)["path"])
        self.assertEqual([], [name for name in inside if other in name])

    def test_readme_inside_says_where_everything_came_from(self):
        text = members(resources.build(self.dist)["path"])["LEIAME.md"].decode("utf-8")
        self.assertIn(REVISION, text)
        self.assertIn("SIL Open Font License", text)
        self.assertIn("MIT", text)
        self.assertIn("fonts/{fontstack}/{range}.pbf", text)

    def test_same_assets_give_the_same_archive_byte_for_byte(self):
        first = resources.build(self.dist)["path"].read_bytes()
        (self.root / "raw").joinpath(f"basemaps-assets-{REVISION}.tar.gz").unlink()
        second = resources.build(self.root / "outra")["path"].read_bytes()
        self.assertEqual(first, second)
        self.assertEqual(b"\x00\x00\x00\x00", first[4:8])  # o gzip não guarda a data

    def test_missing_glyph_range_is_refused(self):
        self.publish(upstream_files(without=["fonts/Noto Sans Regular/8192-8447.pbf"]))
        with self.assertRaises(RuntimeError) as ctx:
            resources.build(self.dist)
        self.assertIn("fonts/Noto Sans Regular/8192-8447.pbf", str(ctx.exception))
        self.assertFalse((self.dist / "carcara-recursos.tar.gz").exists())

    def test_missing_sprite_sheet_is_refused(self):
        self.publish(upstream_files(without=["sprites/v4/dark@2x.png"]))
        with self.assertRaises(RuntimeError) as ctx:
            resources.build(self.dist)
        self.assertIn("sprites/v4/dark@2x.png", str(ctx.exception))

    def test_content_different_from_the_pinned_one_is_refused(self):
        # A revisão é fixa; se o conteúdo baixado não é o que foi conferido, algo mudou no caminho.
        changed = upstream_files(extra={"sprites/v4/light.png": sheet("outra", "coisa")})
        self.publish(changed, pin=False)
        with self.assertRaises(RuntimeError) as ctx:
            resources.build(self.dist)
        self.assertIn("ASSETS_CONTENT_SHA256", str(ctx.exception))
        self.assertFalse((self.dist / "carcara-recursos.tar.gz").exists())

    def test_links_and_paths_outside_the_folders_never_get_in(self):
        files = upstream_files(extra={"fonts/../../fora.pbf": b"x", "sprites/v4/../../fora.png": b"y"})
        self.publish(files, links=[("sprites/v4/atalho.png", "/etc/passwd")])
        inside = members(resources.build(self.dist)["path"])
        self.assertNotIn("sprites/v4/atalho.png", inside)
        self.assertFalse(any(".." in name for name in inside), sorted(inside)[:5])

    def test_download_that_is_not_an_archive_is_refused_and_not_kept(self):
        good = self.server.files[f"/{REVISION}.tar.gz"]
        self.server.files[f"/{REVISION}.tar.gz"] = b"<html>manutencao</html>"
        with self.assertRaises(RuntimeError):
            resources.build(self.dist)
        # O download estragado não fica valendo: na vez seguinte, com a origem de volta, baixa de novo e monta.
        self.server.files[f"/{REVISION}.tar.gz"] = good
        self.assertEqual(20, resources.build(self.dist)["sprite_files"])

    def test_archive_already_downloaded_is_reused(self):
        resources.build(self.dist)
        resources.build(self.dist)
        self.assertEqual(1, sum(1 for path, _ in self.server.requests if path.endswith(".tar.gz")))


    def test_pack_has_the_styles_and_the_own_sprites_and_keeps_the_upstream_ones(self):
        files = upstream_files()
        inside = members(resources.build(self.dist)["path"])
        for flavor in styles.FLAVORS:
            self.assertEqual((styles.STYLES_DIR / f"{flavor}.json").read_bytes(), inside[f"styles/{flavor}.json"])
        self.assertIn(b"BSD", inside["styles/LICENCA.md"])
        for flavor in styles.OWN_SPRITE_FLAVORS:
            for density in ("", "@2x"):
                index = json.loads(inside[f"sprites/carcara-v4/{flavor}{density}.json"])
                self.assertEqual(set(styles.OWN_ICONS), set(index))
                composed = png.decode(inside[f"sprites/carcara-v4/{flavor}{density}.png"])
                upstream = png.decode(files[f"sprites/v4/{flavor}{density}.png"])
                # A folha de origem fica no canto de cima, como estava; os ícones próprios vêm embaixo.
                self.assertEqual(upstream.pixel(0, 0), composed.pixel(0, 0))
                self.assertTrue(all(entry["y"] > upstream.height for entry in index.values()))
        # A estrutura de antes não muda: o que vem da origem continua no mesmo caminho, com os mesmos bytes.
        for name, data in resources.select(files).items():
            self.assertEqual(data, inside[name], name)
        self.assertEqual([], [name for name in inside if name.startswith("sprites/carcara-v4/")
                              and name.split("/")[-1].split(".")[0].split("@")[0] not in styles.OWN_SPRITE_FLAVORS])

    def test_reports_the_styles(self):
        self.assertEqual(len(styles.FLAVORS), resources.build(self.dist)["style_files"])

    def test_readme_inside_explains_the_styles(self):
        text = members(resources.build(self.dist)["path"])["LEIAME.md"].decode("utf-8")
        self.assertIn("styles/", text)
        self.assertIn("{recursos}", text)
        self.assertIn("{tiles}", text)
        self.assertIn("BSD", text)

    def test_upstream_sheet_that_does_not_read_is_refused(self):
        self.publish(upstream_files(extra={"sprites/v4/dark.png": b"isto nao e png"}))
        with self.assertRaises(RuntimeError) as ctx:
            resources.build(self.dist)
        self.assertIn("sprites/v4/dark", str(ctx.exception))
        self.assertFalse((self.dist / "carcara-recursos.tar.gz").exists())


class DeterministicGzipTest(unittest.TestCase):
    def test_written_archive_reads_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "x.tar.gz"
            resources.write_archive({"b/2.txt": b"dois", "a/1.txt": b"um"}, dest)
            self.assertEqual({"a/1.txt": b"um", "b/2.txt": b"dois"}, members(dest))
            with gzip.open(dest) as gz, tarfile.open(fileobj=gz) as tar:
                self.assertEqual(["a/1.txt", "b/2.txt"], tar.getnames())  # ordem fixa
                self.assertTrue(all(m.mtime == 0 for m in tar.getmembers()))


if __name__ == "__main__":
    unittest.main()
