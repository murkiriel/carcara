"""O mínimo de PNG para juntar ícones a uma folha de ícones: ler uma imagem de 8 bits por canal e gravar em RGBA.

Lê os tipos que as folhas de ícones de origem usam (RGBA e paleta, com ou sem transparência; também cinza e RGB),
sem entrelaçamento. Grava sempre RGBA de 8 bits, com o mesmo filtro em toda linha e o zlib no nível máximo: a mesma
imagem dá sempre os mesmos bytes.
"""
from __future__ import annotations

import struct
import zlib
from typing import List, Tuple

SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Canais por pixel de cada tipo de cor (0 cinza, 2 RGB, 3 paleta, 4 cinza com alfa, 6 RGBA).
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class Image:
    """Uma imagem RGBA de 8 bits: `pixels` tem 4 bytes por pixel, linha a linha, de cima para baixo."""

    def __init__(self, width: int, height: int, pixels: bytes = b""):
        self.width, self.height = width, height
        self.pixels = bytearray(pixels) if pixels else bytearray(width * height * 4)
        if len(self.pixels) != width * height * 4:
            raise ValueError(f"{len(self.pixels)} bytes não formam uma imagem RGBA de {width}x{height}")

    def paste(self, other: "Image", x: int, y: int) -> None:
        """Copia `other` para a posição (x, y), substituindo o que havia. A cópia tem de caber inteira."""
        if x < 0 or y < 0 or x + other.width > self.width or y + other.height > self.height:
            raise ValueError(f"a imagem de {other.width}x{other.height} não cabe em ({x}, {y}) numa de "
                             f"{self.width}x{self.height}")
        row = other.width * 4
        for line in range(other.height):
            start = ((y + line) * self.width + x) * 4
            self.pixels[start:start + row] = other.pixels[line * row:(line + 1) * row]

    def pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        start = (y * self.width + x) * 4
        return tuple(self.pixels[start:start + 4])  # type: ignore[return-value]


def _chunks(data: bytes):
    if data[:8] != SIGNATURE:
        raise ValueError("não é um PNG")
    position = 8
    while position + 8 <= len(data):
        size, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + size]
        if len(body) != size:
            raise ValueError("PNG truncado")
        yield kind, body
        position += 12 + size
        if kind == b"IEND":
            return
    raise ValueError("PNG sem o fim (IEND)")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> List[bytearray]:
    stride = width * bpp
    rows: List[bytearray] = []
    previous = bytearray(stride)
    position = 0
    for _ in range(height):
        kind = raw[position]
        line = bytearray(raw[position + 1:position + 1 + stride])
        if len(line) != stride:
            raise ValueError("PNG com dados de imagem truncados")
        position += 1 + stride
        if kind == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 0xFF
        elif kind == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 0xFF
        elif kind == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                up_left = previous[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, previous[i], up_left)) & 0xFF
        elif kind != 0:
            raise ValueError(f"filtro de linha desconhecido: {kind}")
        rows.append(line)
        previous = line
    return rows


def decode(data: bytes) -> Image:
    """Lê um PNG de 8 bits por canal, sem entrelaçamento, e devolve a imagem em RGBA."""
    header = None
    palette = b""
    transparency = b""
    compressed = bytearray()
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            transparency = body
        elif kind == b"IDAT":
            compressed += body
    if header is None:
        raise ValueError("PNG sem cabeçalho (IHDR)")
    width, height, depth, color, _, _, interlace = header
    if depth != 8 or color not in _CHANNELS or interlace != 0:
        raise ValueError(f"PNG não suportado: {depth} bits, tipo de cor {color}, entrelaçamento {interlace}")
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as e:
        raise ValueError(f"PNG com dados de imagem estragados ({e})") from e
    channels = _CHANNELS[color]
    rows = _unfilter(raw, width, height, channels)
    pixels = bytearray()
    for line in rows:
        if color == 6:
            pixels += line
        elif color == 2:
            for i in range(0, len(line), 3):
                pixels += line[i:i + 3] + b"\xff"
        elif color == 0:
            for value in line:
                pixels += bytes((value, value, value, 255))
        elif color == 4:
            for i in range(0, len(line), 2):
                pixels += bytes((line[i], line[i], line[i], line[i + 1]))
        else:
            for index in line:
                if 3 * index + 3 > len(palette):
                    raise ValueError("PNG com índice fora da paleta")
                alpha = transparency[index] if index < len(transparency) else 255
                pixels += palette[3 * index:3 * index + 3] + bytes((alpha,))
    return Image(width, height, bytes(pixels))


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def encode(image: Image) -> bytes:
    """Grava a imagem como PNG RGBA de 8 bits. Filtro "sub" em toda linha, zlib nível 9: saída reproduzível."""
    stride = image.width * 4
    raw = bytearray()
    for line in range(image.height):
        row = image.pixels[line * stride:(line + 1) * stride]
        raw.append(1)
        raw += bytes(row[i] if i < 4 else (row[i] - row[i - 4]) & 0xFF for i in range(stride))
    header = struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)
    return SIGNATURE + _chunk(b"IHDR", header) + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")
