import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from carcara import config, net, sources  # noqa: E402
from carcara.util import file_hash  # noqa: E402
from tests.fake_server import FakeServer  # noqa: E402


def fake_mesh(exclude=()) -> bytes:
    """GeoJSON no formato da API de malhas do IBGE: uma feição por UF, código em `codarea`."""
    features = [{"type": "Feature", "properties": {"codarea": code},
                 "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}
                for code in config.IBGE_STATE_CODES if code not in exclude]
    return json.dumps({"type": "FeatureCollection", "features": features}).encode()


class MeshTest(unittest.TestCase):
    """sources.ibge_mesh: a malha é a cópia versionada, conferida (27 UFs e sha256) e sem nenhum acesso à rede, como
    no Andorinha.

    Até 2026-11-09 a malha vinha da API do IBGE; de 2026-11-04 em diante a API não respondeu aos executores do
    GitHub Actions e todas as gerações agendadas falharam."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self._tmp.name) / "ibge_malha_uf.json"
        self._patches = [mock.patch.object(config, "IBGE_MESH_COPY", self.copy),
                         mock.patch.object(net, "download", side_effect=AssertionError("baixou a malha")),
                         mock.patch.object(net, "fetch_text", side_effect=AssertionError("acessou a rede"))]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        self._tmp.cleanup()

    def write_copy(self, content: bytes, sha256: str = "") -> None:
        self.copy.write_bytes(content)
        patch = mock.patch.object(config, "IBGE_MESH_COPY_SHA256", sha256 or hashlib.sha256(content).hexdigest())
        patch.start()
        self._patches.append(patch)

    def test_good_copy_is_used_without_network(self):
        self.write_copy(fake_mesh())
        self.assertEqual(self.copy, sources.ibge_mesh())

    def test_copy_missing_a_state_stops(self):
        self.write_copy(fake_mesh(exclude=("53",)))  # sem o DF
        with self.assertRaises(RuntimeError) as ctx:
            sources.ibge_mesh()
        self.assertIn("DF", str(ctx.exception))

    def test_copy_that_is_not_json_stops(self):
        self.write_copy(b"<html><body>Servico indisponivel</body></html>")
        with self.assertRaises(RuntimeError) as ctx:
            sources.ibge_mesh()
        self.assertIn("JSON", str(ctx.exception))

    def test_missing_copy_stops(self):
        with self.assertRaises(RuntimeError) as ctx:
            sources.ibge_mesh()
        self.assertIn(self.copy.name, str(ctx.exception))

    def test_copy_changed_without_new_sha256_stops(self):
        """Uma malha diferente muda a divisão dos pacotes: só entra com o sha256 novo no config, de propósito."""
        self.write_copy(fake_mesh(), sha256="0" * 64)
        with self.assertRaises(RuntimeError) as ctx:
            sources.ibge_mesh()
        self.assertIn("sha256", str(ctx.exception))


class VersionedMeshTest(unittest.TestCase):
    """A cópia da malha que vai no repositório (config.IBGE_MESH_COPY)."""

    def test_has_the_27_states(self):
        self.assertIsNone(sources.mesh_problem(config.IBGE_MESH_COPY))

    def test_is_the_reviewed_file(self):
        """Trocar a cópia é decisão consciente: baixar da URL do config, conferir e atualizar o sha256."""
        self.assertEqual(config.IBGE_MESH_COPY_SHA256, file_hash(config.IBGE_MESH_COPY, "sha256"))

    def test_is_the_mesh_of_the_published_generations(self):
        """A mesma malha que gerou as releases de outubro e a do Andorinha: a divisão dos pacotes não muda."""
        self.assertEqual("4435b2e0e62de6d68f5c5387e01efc31655242948ae9434b78a3b5b05582e497",
                         config.IBGE_MESH_COPY_SHA256)

    def test_is_versioned_outside_data(self):
        """gerador/data/ fica fora do git; a cópia não pode morar lá."""
        self.assertNotIn("data", config.IBGE_MESH_COPY.relative_to(config.GENERATOR_DIR).parts)

    def test_generation_uses_the_real_copy(self):
        with mock.patch.object(net, "download", side_effect=AssertionError("baixou a malha")):
            self.assertEqual(config.IBGE_MESH_COPY, sources.ibge_mesh())


def build(key, uploaded, version="4.15.2", **extra):
    entry = {"key": key, "size": 138_000_000_000, "md5sum": "x", "b3sum": "ab" * 32, "uploaded": uploaded,
             "version": version}
    entry.update(extra)
    return entry


class LatestBuildTest(unittest.TestCase):
    """sources.latest_build: a entrada mais recente do índice de builds, só se for do esquema esperado."""

    def setUp(self):
        self.server = FakeServer().__enter__()
        self._patches = [mock.patch.object(config, "BUILDS_INDEX_URL", self.server.url("/builds.json")),
                         mock.patch.object(config, "BUILD_BASE_URL", "https://exemplo.invalid/"),
                         mock.patch.object(sources, "RETRY_DELAY", 0)]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.server.__exit__(None, None, None)

    def publish(self, entries):
        self.server.files["/builds.json"] = json.dumps(entries).encode()

    def test_picks_the_most_recent_upload(self):
        # O índice não vem em ordem: a escolha é pela data de envio, não pela posição.
        self.publish([build("20230918.pmtiles", "2023-09-18T10:00:00.000Z", version="3.0.0"),
                      build("20261001.pmtiles", "2026-10-01T08:53:09.033Z"),
                      build("20260930.pmtiles", "2026-09-30T08:58:27.530Z")])
        latest = sources.latest_build()
        self.assertEqual("20261001.pmtiles", latest["key"])
        self.assertEqual("https://exemplo.invalid/20261001.pmtiles", latest["url"])
        self.assertEqual("4.15.2", latest["version"])
        self.assertEqual("ab" * 32, latest["b3sum"])
        self.assertEqual("2026-10-01T08:53:09.033Z", latest["uploaded"])
        self.assertEqual(138_000_000_000, latest["size"])

    def test_other_major_version_is_refused(self):
        self.publish([build("20270101.pmtiles", "2027-01-01T09:00:00.000Z", version="5.0.0"),
                      build("20261001.pmtiles", "2026-10-01T08:53:09.033Z")])
        with self.assertRaises(RuntimeError) as ctx:
            sources.latest_build()
        self.assertIn("5.0.0", str(ctx.exception))

    def test_empty_index_is_refused(self):
        self.publish([])
        with self.assertRaises(RuntimeError):
            sources.latest_build()

    def test_index_that_is_not_a_list_is_refused(self):
        self.server.files["/builds.json"] = b"<html>manutencao</html>"
        with self.assertRaises(RuntimeError):
            sources.latest_build()

    def test_entry_without_b3sum_is_refused(self):
        entry = build("20261001.pmtiles", "2026-10-01T08:53:09.033Z")
        del entry["b3sum"]
        self.publish([entry])
        with self.assertRaises(RuntimeError) as ctx:
            sources.latest_build()
        self.assertIn("b3sum", str(ctx.exception))

    def test_key_with_path_is_refused(self):
        # O `key` vira parte de um endereço: só um nome de arquivo simples é aceito.
        self.publish([build("../outro/20261001.pmtiles", "2026-10-01T08:53:09.033Z")])
        with self.assertRaises(RuntimeError):
            sources.latest_build()


if __name__ == "__main__":
    unittest.main()
