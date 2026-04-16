class Compiler:
    '''
    
    '''
    
    BITS = 5
    MASK = (1 << BITS) - 1  # 0b11111

    def __init__(self):
        self.data = None      # bytearray
        self.length = 0       # número de elementos (no bytes)

    # --------------------------------------------------
    # 1) Convertir lista de ints -> formato empaquetado
    # --------------------------------------------------
    def from_list(self, values: list[int]):
        self.length = len(values)
        total_bits = self.length * self.BITS
        total_bytes = (total_bits + 7) // 8

        self.data = bytearray(total_bytes)

        for i, v in enumerate(values):
            if v < 0 or v > self.MASK:
                raise ValueError(f"Valor fuera de rango: {v}")
            self._set(i, v)

    # --------------------------------------------------
    # 2) Guardar en fichero
    # --------------------------------------------------
    def guardar(self, filepath: str):
        if self.data is None:
            raise ValueError("No hay datos")

        with open(filepath, "wb") as f:
            # guardamos longitud primero (8 bytes)
            f.write(self.length.to_bytes(8, "little"))
            f.write(self.data)

    # --------------------------------------------------
    # 3) Cargar desde fichero
    # --------------------------------------------------
    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            self.length = int.from_bytes(f.read(8), "little")
            self.data = bytearray(f.read())

    # --------------------------------------------------
    # 4) Debug: imprimir contenido
    # --------------------------------------------------
    def debug_print(self, limit=50):
        if self.data is None:
            print("No hay datos")
            return

        print("=== DEBUG DNA ===")
        print(f"Longitud: {self.length}")
        print(f"Bytes: {len(self.data)}")

        # imprimir binario
        print("\nBinario (primeros bytes):")
        for b in self.data[:min(16, len(self.data))]:
            print(f"{b:08b}", end=" ")
        print()

        # imprimir valores decodificados
        print("\nValores decimales:")
        for i in range(min(self.length, limit)):
            print(self._get(i), end=" ")
        print("\n=================")

    # --------------------------------------------------
    # Internos: acceso bit a bit
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
    
    
def compiler_test():
    print("a?")
    adn_lista = [0,1,1,1,0,2,1,0,1]
    print("lista: " + str(adn_lista))
    