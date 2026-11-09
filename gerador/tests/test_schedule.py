"""A regra do agendamento: gera toda semana, no domingo (Brasília), e nos dias seguintes até sair, se o domingo falhar,
como no Andorinha. E nunca gera sozinho a primeira geração, nem com um catálogo que não dá para ler (regra própria do
Carcará).

Até 2026-11-09 a regra era "29 dias desde a geração publicada", com uma geração extra marcada (GENERATE_FROM); os testes
dela saíram com ela. Datas de referência: 2026-11-01, 2026-11-08 e 2026-11-15 são domingos. O agendamento dispara às
06:17 e às 12:17 UTC (03:17 e 09:17 em Brasília)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

GENERATOR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GENERATOR))
from carcara import config, schedule  # noqa: E402

LAST_WEEK = "2026-11-01T07:30:00Z"   # geração de domingo, 01/11
THIS_WEEK = "2026-11-08T07:30:00Z"   # geração de domingo, 08/11


def utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class WeekStartTest(unittest.TestCase):
    """schedule.week_start: o domingo, 00:00 em Brasília, mais recente (ou o de agora)."""

    def test_brasilia_is_three_hours_behind_utc(self):
        self.assertEqual(timedelta(hours=-3), schedule.BRASILIA.utcoffset(None))

    def test_on_sunday_it_is_the_same_day(self):
        self.assertEqual(utc("2026-11-08T03:00:00Z"), schedule.week_start(utc("2026-11-08T06:17:00Z")))

    def test_in_the_middle_of_the_week_it_is_the_last_sunday(self):
        self.assertEqual(utc("2026-11-08T03:00:00Z"), schedule.week_start(utc("2026-11-11T15:00:00Z")))

    def test_saturday_night_in_brasilia_is_still_the_previous_week(self):
        """Sábado, 23:00 em Brasília, já é domingo em UTC: a semana ainda é a do domingo anterior."""
        self.assertEqual(utc("2026-11-01T03:00:00Z"), schedule.week_start(utc("2026-11-08T02:00:00Z")))


class GenerationDueTest(unittest.TestCase):
    def due(self, built_at, now, status=schedule.OK, **kwargs):
        return schedule.generation_due(status, built_at, utc(now), **kwargs)[0]

    def test_sunday_generates_when_the_published_is_from_last_week(self):
        self.assertTrue(self.due(LAST_WEEK, "2026-11-08T06:17:00Z"))

    def test_second_sunday_run_stops_after_the_publication(self):
        self.assertFalse(self.due(THIS_WEEK, "2026-11-08T12:17:00Z"))

    def test_the_rest_of_the_week_waits(self):
        for day in range(9, 15):  # segunda, 09/11, a sábado, 14/11
            for hour in ("06:17", "12:17"):
                self.assertFalse(self.due(THIS_WEEK, f"2026-11-{day:02d}T{hour}:00Z"), f"{day}/11 {hour}")
        self.assertFalse(self.due(THIS_WEEK, "2026-11-15T02:59:00Z"))  # sábado, 23:59 em Brasília

    def test_next_sunday_generates(self):
        self.assertTrue(self.due(THIS_WEEK, "2026-11-15T06:17:00Z"))

    def test_failed_sunday_is_retried_on_the_following_days(self):
        self.assertTrue(self.due(LAST_WEEK, "2026-11-08T12:17:00Z"))
        self.assertTrue(self.due(LAST_WEEK, "2026-11-09T06:17:00Z"))
        self.assertTrue(self.due(LAST_WEEK, "2026-11-12T12:17:00Z"))

    def test_a_generation_weeks_old_generates(self):
        """A publicada hoje (2026-10-06) tem semanas: o primeiro disparo depois da mudança já gera."""
        self.assertTrue(self.due("2026-10-06T13:29:08Z", "2026-11-10T06:17:00Z"))

    def test_saturday_night_utc_is_not_sunday_yet(self):
        """Sábado, 22:00 em Brasília: com UTC no lugar de Brasília, geraria um dia antes."""
        self.assertFalse(self.due(LAST_WEEK, "2026-11-08T01:00:00Z"))

    def test_the_week_starts_at_sunday_midnight_in_brasilia(self):
        self.assertFalse(self.due("2026-11-08T03:00:00Z", "2026-11-08T12:17:00Z"))
        self.assertTrue(self.due("2026-11-08T02:59:59Z", "2026-11-08T12:17:00Z"))

    def test_a_manual_generation_in_the_week_does_not_delay_sunday(self):
        self.assertTrue(self.due("2026-11-11T15:00:00Z", "2026-11-15T06:17:00Z"))

    def test_no_published_generation_does_not_generate_on_schedule(self):
        # Regra própria do Carcará: a primeira geração é sempre disparada à mão.
        due, reason = schedule.generation_due(schedule.MISSING, None, utc("2026-11-15T06:17:00Z"))
        self.assertFalse(due)
        self.assertIn("à mão", reason)

    def test_unreadable_catalog_does_not_generate_on_schedule(self):
        due, reason = schedule.generation_due(schedule.UNREADABLE, None, utc("2026-11-15T06:17:00Z"))
        self.assertFalse(due)
        self.assertIn("catálogo", reason)

    def test_date_in_another_format_counts_as_unreadable(self):
        self.assertFalse(self.due("ontem", "2026-11-15T06:17:00Z"))

    def test_manual_always_generates(self):
        self.assertTrue(self.due(THIS_WEEK, "2026-11-08T12:17:00Z", manual=True))
        self.assertTrue(self.due(None, "2026-11-08T12:17:00Z", status=schedule.MISSING, manual=True))
        self.assertTrue(self.due(None, "2026-11-08T12:17:00Z", status=schedule.UNREADABLE, manual=True))

    def test_reasons_say_the_sundays(self):
        due, reason = schedule.generation_due(schedule.OK, LAST_WEEK, utc("2026-11-09T06:17:00Z"))
        self.assertTrue(due)
        self.assertIn("08/11", reason)
        due, reason = schedule.generation_due(schedule.OK, THIS_WEEK, utc("2026-11-10T06:17:00Z"))
        self.assertFalse(due)
        self.assertIn("15/11", reason)

    def test_the_29_day_rule_is_gone(self):
        self.assertFalse(hasattr(config, "GENERATION_INTERVAL_DAYS"))


class PublishedCatalogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.catalog = Path(self._tmp.name) / "catalogo.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_built_at(self):
        self.catalog.write_text(json.dumps({"built_at": THIS_WEEK}), encoding="utf-8")
        self.assertEqual((schedule.OK, THIS_WEEK), schedule.read_published(self.catalog))

    def test_missing_catalog(self):
        self.assertEqual((schedule.MISSING, None), schedule.read_published(self.catalog))

    def test_broken_catalog(self):
        self.catalog.write_text("<html>", encoding="utf-8")
        self.assertEqual((schedule.UNREADABLE, None), schedule.read_published(self.catalog))

    def test_catalog_without_the_date(self):
        self.catalog.write_text(json.dumps({"schema": 1}), encoding="utf-8")
        self.assertEqual((schedule.UNREADABLE, None), schedule.read_published(self.catalog))

    def test_catalog_that_is_not_an_object(self):
        self.catalog.write_text("[1, 2]", encoding="utf-8")
        self.assertEqual((schedule.UNREADABLE, None), schedule.read_published(self.catalog))


class DueScriptTest(unittest.TestCase):
    """A linha de comando que o workflow chama: imprime o motivo e grava run=true|false em $GITHUB_OUTPUT."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.output = self.tmp / "github_output"

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, content, *args):
        catalog = self.tmp / "catalogo.json"
        catalog.unlink(missing_ok=True)
        self.output.unlink(missing_ok=True)  # o script acrescenta ao arquivo, como o Actions espera
        if content is not None:
            catalog.write_text(content, encoding="utf-8")
        env = {**os.environ, "GITHUB_OUTPUT": str(self.output)}
        done = subprocess.run([sys.executable, str(GENERATOR / "scripts" / "due.py"), "--catalog", str(catalog), *args],
                              capture_output=True, text=True, encoding="utf-8", env=env)
        written = self.output.read_text(encoding="utf-8") if self.output.exists() else ""
        return done.returncode, written, done.stdout

    def stamp(self, days_ago: int) -> str:
        built_at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return json.dumps({"built_at": built_at})

    def test_generation_from_this_week(self):
        # Acabou de sair: é sempre desta semana, qualquer que seja o dia em que o teste roda.
        code, output, log = self.run_script(self.stamp(0))
        self.assertEqual((0, "run=false\n"), (code, output))
        self.assertIn("domingo", log)

    def test_generation_from_before_last_sunday(self):
        # Oito dias atrás é sempre de antes do último domingo.
        self.assertEqual((0, "run=true\n"), self.run_script(self.stamp(8))[:2])

    def test_no_catalog_does_not_run_and_is_not_an_error(self):
        code, output, log = self.run_script(None)
        self.assertEqual((0, "run=false\n"), (code, output))
        self.assertIn("à mão", log)

    def test_broken_catalog_does_not_run_and_fails_the_job(self):
        # Um catálogo estragado na raiz não pode passar em silêncio: o job fica vermelho, e ninguém gera por engano.
        code, output, _ = self.run_script("<html>")
        self.assertEqual("run=false\n", output)
        self.assertEqual(1, code)

    def test_manual(self):
        self.assertEqual((0, "run=true\n"), self.run_script(self.stamp(0), "--manual")[:2])
        self.assertEqual((0, "run=true\n"), self.run_script(None, "--manual")[:2])

    def test_the_old_options_are_gone(self):
        for option in ("--generate-from", "--interval-days"):
            self.assertEqual(2, self.run_script(self.stamp(0), option, "1")[0], option)


if __name__ == "__main__":
    unittest.main()
