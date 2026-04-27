'''
    benchmark:
        1.000 millones: 876 segundos para la lectura, en ~24.000 bloques
'''


class PackedDNA:
    BITS = 5
    MASK = (1 << BITS) - 1  # 0b11111
    HEADER_BYTES = 8         # 8 bytes para almacenar length

    def __init__(self):
        self.data = None
        self.length = 0

        # estado lectura secuencial
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0
        self._read_count = 0

    # --------------------------------------------------
    # construir desde lista
    # --------------------------------------------------
    def from_list(self, values: list[int]):
        self.length = len(values)
        total_bits = self.length * self.BITS
        total_bytes = (total_bits + 7) // 8

        self.data = bytearray(total_bytes)

        for i, v in enumerate(values):
            self._set(i, v)

    # --------------------------------------------------
    # guardar / cargar completo en memoria
    # --------------------------------------------------
    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            f.write(self.length.to_bytes(self.HEADER_BYTES, "little"))
            f.write(self.data)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            self.length = int.from_bytes(f.read(self.HEADER_BYTES), "little")
            self.data = bytearray(f.read())

    # --------------------------------------------------
    # lectura de rango [inicio, fin) sin cargar todo en memoria
    # inicio y fin son indices de elementos de adn (no bytes)
    # --------------------------------------------------
    @staticmethod
    def leer_rango(filepath: str, inicio: int, fin: int) -> list[int]:
        """
        Lee los elementos ADN en el rango [inicio, fin) directamente
        desde el fichero sin cargarlo completo en memoria.
        """
        if fin <= inicio:
            return []

        n = fin - inicio

        with open(filepath, "rb") as f:
            # leer length de la cabecera
            length = int.from_bytes(f.read(PackedDNA.HEADER_BYTES), "little")

            if inicio >= length:
                raise ValueError(
                    f"inicio={inicio} fuera del rango del ADN (length={length})"
                )
            if fin > length:
                raise ValueError(
                    f"fin={fin} fuera del rango del ADN (length={length})"
                )

            # calcular byte exacto donde empieza el elemento 'inicio'
            bit_inicio = inicio * PackedDNA.BITS
            byte_inicio = bit_inicio // 8
            bit_offset = bit_inicio % 8   # bits a descartar del primer byte

            # seek al byte correcto (cabecera + offset)
            f.seek(PackedDNA.HEADER_BYTES + byte_inicio)

            # calcular cuantos bytes necesitamos leer
            # n elementos * 5 bits + bits_offset iniciales + 7 para redondear arriba
            bits_necesarios = n * PackedDNA.BITS + bit_offset
            bytes_necesarios = (bits_necesarios + 7) // 8
            raw = f.read(bytes_necesarios)

        # decodificar
        out = [0] * n
        mask = PackedDNA.MASK
        bitbuf = 0
        bits_in_buf = 0
        byte_pos = 0

        # cargar primer byte descartando los bits de offset
        if byte_pos < len(raw):
            bitbuf = raw[byte_pos] >> bit_offset
            bits_in_buf = 8 - bit_offset
            byte_pos += 1

        for i in range(n):
            while bits_in_buf < 5 and byte_pos < len(raw):
                bitbuf |= raw[byte_pos] << bits_in_buf
                bits_in_buf += 8
                byte_pos += 1

            out[i] = bitbuf & mask
            bitbuf >>= 5
            bits_in_buf -= 5

        return out

    # --------------------------------------------------
    # abrir fichero para lectura streaming por chunks
    # devuelve un PackedDNAStream — usado por Genoma
    # --------------------------------------------------
    @staticmethod
    def abrir_stream(filepath: str, chunk_size: int = 4096) -> "PackedDNAStream":
        return PackedDNAStream(filepath, chunk_size)

    # --------------------------------------------------
    # reset lectura en memoria
    # --------------------------------------------------
    def reset_lectura(self):
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0
        self._read_count = 0

    # --------------------------------------------------
    # lectura por bloque optimizada (en memoria)
    # --------------------------------------------------
    def leer_bloque_fast(self, n: int = 4096) -> list[int]:
        if self.data is None:
            raise ValueError("No hay datos cargados en memoria")

        remaining = self.length - self._read_count
        if remaining <= 0:
            return []

        n = min(n, remaining)
        out = [0] * n

        data = self.data
        byte_pos = self._byte_pos
        bitbuf = self._bitbuf
        bits_in_buf = self._bits_in_buf
        mask = self.MASK

        for i in range(n):
            while bits_in_buf < 5:
                if byte_pos >= len(data):
                    break
                bitbuf |= data[byte_pos] << bits_in_buf
                bits_in_buf += 8
                byte_pos += 1

            out[i] = bitbuf & mask
            bitbuf >>= 5
            bits_in_buf -= 5

        self._byte_pos = byte_pos
        self._bitbuf = bitbuf
        self._bits_in_buf = bits_in_buf
        self._read_count += n

        return out

    # --------------------------------------------------
    # debug
    # --------------------------------------------------
    def debug_print(self, limit=50):
        self.reset_lectura()
        vals = self.leer_bloque_fast(limit)

        print("Bits:")
        print(" | ".join(f"{v:05b}" for v in vals))
        print("Dec:")
        print(" | ".join(str(v) for v in vals))

    # --------------------------------------------------
    # metodos internos
    # --------------------------------------------------
    def _set(self, i: int, value: int):
        bit_pos = i * self.BITS
        byte_pos = bit_pos // 8
        offset = bit_pos % 8

        val = (value & self.MASK) << offset

        self.data[byte_pos] &= ~(self.MASK << offset) & 0xFF
        self.data[byte_pos] |= val & 0xFF

        if offset > 3:
            self.data[byte_pos + 1] &= ~(self.MASK >> (8 - offset))
            self.data[byte_pos + 1] |= val >> 8

    def _get(self, i: int) -> int:
        bit_pos = i * self.BITS
        byte_pos = bit_pos // 8
        offset = bit_pos % 8

        val = self.data[byte_pos] >> offset

        if offset > 3:
            val |= self.data[byte_pos + 1] << (8 - offset)

        return val & self.MASK


class PackedDNAStream:
    """
    Lectura streaming de un fichero PackedDNA por chunks.
    Mantiene el fichero abierto mientras dure la compilacion.
    Usado internamente por Genoma.desde_fichero().
    """

    def __init__(self, filepath: str, chunk_size: int = 4096):
        self.filepath = filepath
        self.chunk_size = chunk_size

        self._file = open(filepath, "rb")

        # leer cabecera
        self.length = int.from_bytes(
            self._file.read(PackedDNA.HEADER_BYTES), "little"
        )

        # estado del stream
        self._buffer: list[int] = []
        self._buf_pos = 0          # indice local dentro del buffer actual
        self._global_pos = 0       # indice global — usado para offsets de nodos

        # estado bit a bit del fichero
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0

        # cargar primer chunk
        self._cargar_chunk()

    def next(self) -> int:
        """
        Devuelve el siguiente elemento del ADN e incrementa el indice global.
        Lanza ADNAgotadoError si no quedan elementos.
        """
        if self._global_pos >= self.length:
            raise ADNAgotadoError(
                f"ADN agotado en posicion {self._global_pos} "
                f"(length={self.length})"
            )

        # si el buffer local se agoto, pedir siguiente chunk
        if self._buf_pos >= len(self._buffer):
            self._cargar_chunk()
            if not self._buffer:
                raise ADNAgotadoError(
                    f"ADN agotado inesperadamente en posicion {self._global_pos}"
                )

        valor = self._buffer[self._buf_pos]
        self._buf_pos += 1
        self._global_pos += 1
        return valor

    def current_pos(self) -> int:
        """Posicion global actual (indice del proximo elemento sin consumir)."""
        return self._global_pos

    def hay_restante(self) -> bool:
        """True si queda al menos un elemento sin consumir."""
        return self._global_pos < self.length

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    def _cargar_chunk(self):
        """Carga el siguiente chunk desde el fichero al buffer interno."""
        remaining = self.length - self._global_pos - self._buf_pos + (
            len(self._buffer) - self._buf_pos
            if self._buffer else 0
        )

        # calcular cuantos elementos quedan realmente
        elementos_restantes = self.length - (
            self._global_pos - (len(self._buffer) - self._buf_pos)
            if self._buffer else self._global_pos
        )
        n = min(self.chunk_size, max(0, self.length - self._global_pos))

        if n <= 0:
            self._buffer = []
            self._buf_pos = 0
            return

        out = [0] * n
        mask = PackedDNA.MASK

        data_file = self._file
        byte_pos = self._byte_pos
        bitbuf = self._bitbuf
        bits_in_buf = self._bits_in_buf

        for i in range(n):
            while bits_in_buf < 5:
                byte = data_file.read(1)
                if not byte:
                    # fichero terminado antes de lo esperado
                    raise ADNAgotadoError(
                        f"Fichero truncado leyendo elemento {self._global_pos + i}"
                    )
                bitbuf |= byte[0] << bits_in_buf
                bits_in_buf += 8
                byte_pos += 1

            out[i] = bitbuf & mask
            bitbuf >>= 5
            bits_in_buf -= 5

        self._byte_pos = byte_pos
        self._bitbuf = bitbuf
        self._bits_in_buf = bits_in_buf

        self._buffer = out
        self._buf_pos = 0


class ADNAgotadoError(Exception):
    """El ADN se ha agotado antes de terminar la compilacion."""
    pass


class ADNSobranteError(Exception):
    """La compilacion termino pero quedaba ADN sin consumir."""
    pass