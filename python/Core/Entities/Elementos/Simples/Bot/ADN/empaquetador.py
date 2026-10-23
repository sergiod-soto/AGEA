'''
    benchmark:
        1.000 millones: 876 segundos para la lectura, en ~24.000 bloques
'''


class ADNAgotadoError(Exception):
    """Se lanza cuando se intenta leer mas ADN del disponible."""
    pass


class ADNSobranteError(Exception):
    """Se lanza cuando termina la compilacion y queda ADN sin consumir."""
    pass


class PackedDNA:
    BITS = 5
    MASK = (1 << BITS) - 1  # 0b11111
    HEADER_BYTES = 8         # bytes reservados para la longitud total

    def __init__(self):
        self.data = None
        self.length = 0

        # estado lectura secuencial en memoria
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0
        self._read_count = 0

        # lectura streaming desde fichero
        self._file = None
        self._chunk_size = 4096
        self._buf = []
        self._buf_pos = 0
        self._global_pos = 0   # indice absoluto global — referencia para offsets de nodos

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
    # guardar / cargar en memoria
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
    # apertura para streaming desde fichero
    # --------------------------------------------------
    def open(self, filepath: str, chunk_size: int = 4096) -> "PackedDNA":
        """
        Abre el fichero para lectura por chunks sin cargarlo en memoria.
        Pensado para usarse con context manager o con close() manual.
        """
        self._file = open(filepath, "rb")
        self._chunk_size = chunk_size
        self.length = int.from_bytes(self._file.read(self.HEADER_BYTES), "little")
        self._buf = []
        self._buf_pos = 0
        self._global_pos = 0
        return self

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # nunca suprime excepciones

    # --------------------------------------------------
    # lectura secuencial streaming — un elemento a la vez
    # --------------------------------------------------
    def next(self) -> int:
        """
        Devuelve el siguiente elemento del ADN.
        Pide un nuevo chunk al fichero cuando el buffer local se agota.
        Lanza ADNAgotadoError si no queda ADN.
        """
        if self._file is None:
            raise RuntimeError("Fichero no abierto. Usar open() primero.")

        if self._global_pos >= self.length:
            raise ADNAgotadoError(
                f"ADN agotado en posicion {self._global_pos} "
                f"(longitud total: {self.length})"
            )

        if self._buf_pos >= len(self._buf):
            self._cargar_chunk()

        valor = self._buf[self._buf_pos]
        self._buf_pos += 1
        self._global_pos += 1
        return valor

    def elementos_restantes(self) -> int:
        """Cuantos elementos quedan sin consumir."""
        return self.length - self._global_pos

    # --------------------------------------------------
    # leer rango [inicio, fin] con seek directo
    # --------------------------------------------------
    def leer_rango(self, inicio: int, fin: int) -> list[int]:
        """
        Devuelve los elementos en el rango [inicio, fin] inclusive
        haciendo seek directo al byte correspondiente.
        No altera el estado de lectura secuencial.
        Funciona tanto con fichero abierto como con data en memoria.
        """
        if inicio < 0 or fin >= self.length or inicio > fin:
            raise ValueError(
                f"Rango invalido [{inicio}, {fin}] "
                f"para ADN de longitud {self.length}"
            )

        n = fin - inicio + 1

        if self.data is not None:
            # lectura desde memoria — acceso directo
            return [self._get(i) for i in range(inicio, fin + 1)]

        if self._file is not None:
            return self._leer_rango_fichero(inicio, n)

        raise RuntimeError("No hay datos. Usar open() o load() primero.")

    def _leer_rango_fichero(self, inicio: int, n: int) -> list[int]:
        """Seek directo al byte del elemento 'inicio' y decodifica n elementos."""
        bit_inicio = inicio * self.BITS
        byte_inicio = bit_inicio // 8
        offset_inicial = bit_inicio % 8  # bits a descartar del primer byte

        # bytes necesarios para cubrir offset_inicial + n*5 bits
        bits_necesarios = offset_inicial + n * self.BITS
        bytes_necesarios = (bits_necesarios + 7) // 8

        self._file.seek(self.HEADER_BYTES + byte_inicio)
        raw = bytearray(self._file.read(bytes_necesarios))

        out = [0] * n
        mask = self.MASK

        # inicializar buffer descartando los bits del offset
        bitbuf = raw[0] >> offset_inicial
        bits_in_buf = 8 - offset_inicial
        byte_pos = 1

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
    # interno — cargar siguiente chunk desde fichero
    # --------------------------------------------------
    def _cargar_chunk(self):
        inicio = self._global_pos
        fin = min(inicio + self._chunk_size - 1, self.length - 1)
        self._buf = self._leer_rango_fichero(inicio, fin - inicio + 1)
        self._buf_pos = 0

    # --------------------------------------------------
    # reset y lectura por bloque (para data en memoria)
    # --------------------------------------------------
    def reset_lectura(self):
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0
        self._read_count = 0

    def leer_bloque_fast(self, n: int = 4096) -> list[int]:
        if self.data is None:
            raise ValueError(
                "No hay datos en memoria. "
                "leer_bloque_fast solo funciona con load()."
            )

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
    def debug_print(self, limit: int = 50):
        self.reset_lectura()
        vals = self.leer_bloque_fast(limit)
        print("Bits:")
        print(" | ".join(f"{v:05b}" for v in vals))
        print("Dec:")
        print(" | ".join(str(v) for v in vals))

    # --------------------------------------------------
    # metodos internos de acceso a memoria
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
