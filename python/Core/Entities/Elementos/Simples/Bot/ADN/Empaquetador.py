'''
    benchmark:
        1.000 millones: 876 segundos para la lectura, en ~24.000 bloques
'''

    
    
class PackedDNA:
    BITS = 5
    MASK = (1 << BITS) - 1  # 0b11111

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
    # guardar / cargar
    # --------------------------------------------------
    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            f.write(self.length.to_bytes(8, "little"))
            f.write(self.data)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            self.length = int.from_bytes(f.read(8), "little")
            self.data = bytearray(f.read())

    # --------------------------------------------------
    # reset lectura
    # --------------------------------------------------
    def reset_lectura(self):
        self._byte_pos = 0
        self._bitbuf = 0
        self._bits_in_buf = 0
        self._read_count = 0

    # --------------------------------------------------
    # lectura por bloque optimizada (64-bit buffer)
    # --------------------------------------------------
    def leer_bloque_fast(self, n: int = 4096) -> list[int]:
        if self.data is None:
            raise ValueError("No hay datos")

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
            # rellenar buffer hasta tener >=5 bits
            while bits_in_buf < 5:
                if byte_pos >= len(data):
                    break

                # cargar 1 byte
                bitbuf |= data[byte_pos] << bits_in_buf
                bits_in_buf += 8
                byte_pos += 1

            # extraer valor (5 bits)
            out[i] = bitbuf & mask

            # consumir bits
            bitbuf >>= 5
            bits_in_buf -= 5

        # guardar estado
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


# def compiler_test():
#     lectorADN = PackedDNA()

#     adn_lista = []

#     for i in range(1000000000):
#         adn_lista.append(i % 32)
    
#     lectorADN.from_list(adn_lista)
#     lectorADN.save("C:\\Users\\Sergiod\\Desktop\\asdf.bin")
    
#     dna2 = PackedDNA()
#     dna2.load("C:\\Users\\Sergiod\\Desktop\\asdf.bin")
    
#     while True:
#         i += 1
#         bloque = dna2.leer_bloque_fast() 
#         if not bloque:
#             break        

