from array import array

class AdnClass:
    def __init__(self, cromosomas=None):
        if cromosomas is None:
            cromosomas = [0]
        self.cromosomas = array('B', cromosomas)
        self.iterator = 0

    def next_chromosome(self):
        if self.iterator >= len(self.cromosomas):
            raise IndexError(
                f"Error.\nIndexOutOfBoundException.\n\tIterator: {self.iterator}, len(cromosomas): {len(self.cromosomas)}\n"
            )
        value = self.cromosomas[self.iterator]
        self.iterator += 1
        return value