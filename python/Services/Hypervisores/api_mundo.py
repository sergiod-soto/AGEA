from abc import ABC, abstractmethod


class MundoAPI(ABC):

    @abstractmethod
    def mover(self, dx: int, dy: int):
        pass

    @abstractmethod
    def observar(self) -> Observation:
        pass
