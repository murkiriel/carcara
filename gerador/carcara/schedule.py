"""Quando gerar de novo: toda semana, no domingo, como no Andorinha. O agendamento dispara todo dia, e só segue para a
geração quando a publicada (`built_at` do catalogo.json da raiz) é de antes do último domingo, 00:00 em Brasília.
Assim, num domingo normal, gera no primeiro disparo e os seguintes só conferem a data; se o domingo falhar, os dias
seguintes tentam de novo até sair. A linha de comando fica em scripts/due.py.

Até 2026-11-09 a regra era "a cada 29 dias desde a geração publicada", com uma geração extra marcada; mudou para
semanal, como no Andorinha, para os projetos irmãos andarem no mesmo passo e o domingo ficar previsível.

Diferente dos projetos irmãos, de propósito: **sem geração publicada, o agendamento não gera.** A primeira geração é
sempre disparada à mão, para a primeira release nunca sair sozinha. E um catálogo que não dá para ler também não
gera: quem decide é uma pessoa, e o job fica vermelho para ela ver.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

OK, MISSING, UNREADABLE = "ok", "missing", "unreadable"

# O domingo é o de Brasília: sem horário de verão desde 2019, sempre UTC-3.
BRASILIA = timezone(timedelta(hours=-3), "Brasília")


def read_published(catalog: Path) -> Tuple[str, Optional[str]]:
    """(situação, built_at) do catálogo publicado: OK com a data; MISSING se o arquivo não existe; UNREADABLE se
    existe mas não é um catálogo com a data."""
    if not catalog.exists():
        return MISSING, None
    try:
        built_at = json.loads(catalog.read_text(encoding="utf-8")).get("built_at")
    except (OSError, ValueError, AttributeError):
        return UNREADABLE, None
    return (OK, built_at) if isinstance(built_at, str) else (UNREADABLE, None)


def week_start(now: datetime) -> datetime:
    """O domingo mais recente (o de hoje, se hoje é domingo), 00:00 em Brasília, em UTC."""
    local = now.astimezone(BRASILIA)
    sunday = local.date() - timedelta(days=(local.weekday() + 1) % 7)  # weekday(): segunda 0 ... domingo 6
    return datetime(sunday.year, sunday.month, sunday.day, tzinfo=BRASILIA).astimezone(timezone.utc)


def _day(moment: datetime) -> str:
    return moment.astimezone(BRASILIA).strftime("%d/%m")


def _parse(built_at: Optional[str]) -> datetime:
    return datetime.strptime(built_at or "", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def generation_due(status: str, built_at: Optional[str], now: datetime, manual: bool = False) -> Tuple[bool, str]:
    """(gera?, motivo). Gera se a geração publicada é de antes do último domingo (00:00 em Brasília). Nunca faz a
    primeira geração, nem gera com um catálogo ilegível: essas ficam para uma pessoa, à mão."""
    if manual:
        return True, "disparado à mão: gera"
    if status == MISSING:
        return False, "nenhuma geração publicada: a primeira geração é disparada à mão, o agendamento não gera"
    try:
        if status != OK:
            raise ValueError(status)
        built = _parse(built_at)
    except ValueError:
        return False, ("o catálogo publicado não tem uma data legível: o agendamento não gera; conserte o catálogo "
                       "ou dispare à mão")
    start = week_start(now)
    if built < start:
        return True, f"geração publicada em {built_at}, antes do domingo {_day(start)}: gera"
    return False, (f"geração publicada em {built_at}, já nesta semana (desde o domingo {_day(start)}): "
                   f"ainda não, gera no domingo {_day(start + timedelta(days=7))}")


def is_readable(status: str, built_at: Optional[str]) -> bool:
    """A data do catálogo publicado pôde ser lida? (MISSING conta como lido: não há o que ler.)"""
    if status == MISSING:
        return True
    try:
        _parse(built_at)
    except ValueError:
        return False
    return status == OK
