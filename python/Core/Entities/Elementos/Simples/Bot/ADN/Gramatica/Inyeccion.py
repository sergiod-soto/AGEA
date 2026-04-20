from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Elementos import Nodo


def _importsHardCoded():
    return Nodo(
        "_importsBasicos",
        [
            #
            # Tipos y estructuras
            "from functools import reduce\n",
            "from collections import defaultdict, Counter, deque, OrderedDict, namedtuple\n",
            "from itertools import chain, combinations, permutations, product\n\n",
            #
            # Strings y texto
            "import string\n\n",
            #
            # Sistema básico
            "import os\n",
            "import sys\n",
            "import math\n",
            "import time\n",
            "import copy\n",
            "import json\n\n",
            #
            # Utilidades de código
            "from typing import List, Dict, Tuple, Optional, Any, Union\n",
            #
            # Estructuras adicionales
            "from functools import wraps, partial, lru_cache\n\n",
            #
            # Números
            "import statistics\n\n",
            #
            # Control del programa
            "import warnings\n",
            "from abc import ABC, abstractmethod\n\n",
            #
            # Inspección básica
            "import inspect\n",
            "from enum import Enum, auto\n\n",
        ],
    )


def _codigoInyectado():
    return Nodo("_codigoInyectado", [""])
