**🌐 [Español](README.md) · English**

# AGEA

> A living-world simulator where agents controlled by evolving neural networks (**HyperNEAT**) survive and interact with a simulated physical environment: climate, terrain, biomes, and objects with behaviors of their own.

<!-- TODO: add a screenshot or GIF of Unity showing the world. -->
<!-- ![AGEA running](docs/screenshot.png) -->

**Status:** under active development · **Author:** [Sergio Domínguez Soto](https://github.com/sergiod-soto) [[Linkedin](https://www.linkedin.com/in/sergio-dominguez-soto)]

---

## What is AGEA?

AGEA is a simulation environment where **agent intelligence is evolved rather than programmed**. The world is computed turn by turn (*ticks*), is divided into sectors that can run as independent processes, and each agent chooses its actions using a neural network generated through HyperNEAT.

The project was designed from the start to **scale**: the whole system can run on a single machine (local mode) or be distributed across AWS instances (remote mode).

## Features

- **Sector-based world.** A 25,000,000 cell grid (configurable) split into 100×100 sectors computed in parallel.
- **Biomes and soils.** Forest, desert, sea, grassland, jungle, taiga and tundra; stone, sand, mud, grass, gravel, ice, ocean and water soils.
- **Modular chained world generator.** Orograpic and ecological generation split into independent, chained pipeline stages (`orografia`, `mares_interiores`, `rios`, `biomas`, `barro`, `limite`), allowing regeneration or inspection of individual stages or the entire pipeline.
- **Dynamic hydrographic system (River & lake DAG).** Fluvial network and basins modeled as a Directed Acyclic Graph processed topologically from highest to lowest elevation. Lakes retain water below their critical threshold and overflow into emissary rivers upon exceeding it. Discrete terrain projection with anti-flicker hysteresis and inhibition of individual water cell evaporation when managed by hydrology.
- **Per-cell atmospheric system.** Temperature, pressure, wind and humidity (absolute and relative). Solar radiation is computed with the astronomical zenith-angle formula, so seasons emerge on their own (more extreme near the poles, reversed in the southern hemisphere). Air saturation uses Magnus-Tetens and the ideal gas law.
- **Entities built from composable behaviors.** Over 100 reusable modules (health, energy, material, terrain, time, interaction, perception, social, stats…) that combine to define any element in the world.
- **Evolutionary AI.** A custom HyperNEAT implementation on top of `neat-python` and `numpy`: a small network (CPPN) generates the weights of the large network that acts as the agent's brain. Continuous monitoring with extinction alerts when live population reaches zero.
- **Distributed architecture & decoupled execution.** Independent components communicating over **gRPC + Protocol Buffers** (10 `.proto` definitions), with heartbeats, graceful shutdown and centralized logging. Option to disable the bot subsystem (`HABILITAR_BOTS=false`) to run and observe purely geophysical and climatic simulations.
- **Execution control.** Pause, tick-by-tick stepping, bot freezing, snapshot saving and loading, and an interactive console.
- **AWS deployment.** Infrastructure launched on EC2 with storage on S3 through `boto3`.
- **Unity visualization.** A client subscribed to a gRPC stream (`VistaFoco`) receives the region of the world to be displayed in real time.

## Architecture

```mermaid
flowchart TD
    subgraph Client ["🖥️ External Client"]
        Unity["Unity URP Client\n(gRPC Stream / Real-time visualization)"]
    end

    subgraph AWS ["☁️ AWS Infrastructure (Remote / Production Mode)"]
        S3["Amazon S3\n(Snapshots & Storage)"]
        EC2["EC2 Instances\n(Multi-node execution via boto3)"]
    end

    subgraph Backend ["⚙️ Distributed Backend (Python 3.11+ / asyncio)"]
        Main["Main.py\n(Bootstrap, CLI & Modes: local/remote/production)"]
        Config["Config/settings.py\n(Environment variables & Global config)"]

        subgraph InfraLayer ["Infrastructure & Network Layer (gRPC Servers)"]
            Comm["Remote Communications\n(Bidirectional gRPC Bridge / VistaFoco)"]
            Consola["Interactive Console\n(Execution control & commands)"]
            LogSys["Centralized Logging\n(Trace and level management)"]
            
            subgraph GRPCServices ["gRPC Servers (10 .proto definitions)"]
                ServerWorld["World Server\n(Global management and ticks)"]
                ServerSector["Sector Server\n(Parallel sector processing)"]
                ServerBot["Bot / Hypervisor Server\n(Bot lifecycle and control)"]
            end
        end

        subgraph CoreEngine ["Engine & Models Layer (Core)"]
            GM["World Manager\n(Clock, Ticks, Snapshots, Coordination)"]
            GH["Hydrographic Manager\n(River & Lake DAG, Fluvial Dynamics)"]
            Registry["Registries & Caches\n(Catalog and resource manager)"]
            
            subgraph EntitiesSub ["Entities & Physics Model (Entities / Fisica)"]
                Entities["Entities /\nBehaviors (>100 reusable modules)"]
                Biomes["Biomes & Soils\n(Forest, desert, sea, tundra...)"]
                Terrain["Modular Terrain Generator\n(Stages: orography, seas, rivers, biomes)"]
                Hydro["Hydrographic Network\n(Rivers, lakes, overflows, hysteresis)"]
                Atmo["Cell Atmospheric System\n(Temp, pressure, wind, humidity, Magnus-Tetens)"]
                Astronomy["Solar Radiation\n(Zenith angle and astronomical calculation)"]
            end

            LM["World Logic (Logica/)\n(ID assignment, change management and deltas)"]
            
            subgraph AISub ["AI Subsystem (HyperNEAT / NEAT)"]
                GB["Bot Manager\n(Creation, deletion, budgets, extinction alert)"]
                HV["Hypervisor\nHosting and execution of bots"]
                HNEAT["HyperNEAT / NumPy\n(CPPN neural weight generator)"]
            end
        end

        subgraph Testing ["Quality Assurance (Tests/)"]
            Pytest["pytest\n(~400 unit, integration, and E2E tests)"]
        end
    end

    %% Main flow and architecture connections
    Main --> Config
    Main --> Comm
    Main --> GM
    
    Comm <-->|gRPC Streaming| Unity
    GM --> GRPCServices
    GM --> GH
    GH --> Hydro
    GRPCServices --> ServerWorld
    GRPCServices --> ServerSector
    GRPCServices --> ServerBot
    
    GM --> Registry
    Registry --> Entities
    Entities --> Biomes
    Entities --> Terrain
    Entities --> Atmo
    Atmo --> Astronomy
    
    GM --> LM
    LM --> EntitiesSub
    
    GB --> HV
    HV --> HNEAT
    HV --> LM
    
    GM --> S3
    EC2 --> Main
    
    Consola -. Live control .- Main
    LogSys -. Trace collection .- InfraLayer
    Pytest -. Validates robustness .- CoreEngine
```

> The diagram is a simplified view. The exact topology (how many sectors, how many hypervisors, ports, and presence of the bot manager) is defined dynamically in `Infraestructura/Gestores/Bootstrap/topologia.py`.

| Component | Responsibility |
|---|---|
| **World Manager** (`gestor_mundo`) | Drives the simulation clock (pause, tick advance, saving), creates sectors, and coordinates hydrology. |
| **Hydrographic Manager** (`gestor_hidrografico`) | Simulates basin-scale hydrology as a DAG (rivers, lakes with overflow thresholds, water volume propagation). |
| **Sectors** (`sector`) | Each one simulates its slice of terrain and atmosphere and returns the changes (*deltas*) of every tick. |
| **World Logic** (`logica_mundo`) | Maintains gold state, creates, modifies and removes elements, assigns IDs, and stores the hydrographic network. |
| **Bot Manager** (`gestor_bots`) | Spawns and kills bots, distributes compute budgets, handles snapshots, and raises extinction alerts. |
| **Hypervisor** (`hypervisor`) | Hosts and runs the bots (with a configurable limit per instance). |
| **Remote Communications** (`comunicaciones_remoto`) | Single bridge between the local environment and AWS; serves the visualization stream to Unity (`VistaFoco`). |

> Note: the source code (identifiers, folders, comments) is written in Spanish, so the Spanish names are given in parentheses.

## Repository layout

```
AGEA/
├── python/                  # Simulation backend
│   ├── Main.py              # Entry point (local / remote / production modes)
│   ├── Config/              # Centralized configuration (settings.py, environment variables)
│   ├── Core/
│   │   ├── Entities/        # World, biomes, soils, atmosphere and behaviors
│   │   ├── Fisica/          # Thermodynamic functions
│   │   ├── HyperNEAT/       # HyperNEAT implementation
│   │   └── Logica/          # Bot and entity logic
│   ├── Infraestructura/
│   │   ├── Gestores/        # Components, bootstrap, gRPC transport, console and logs
│   │   │   ├── Mundo/       # Gestor_Mundo, Logica_Mundo, Sector and Hidrologia
│   │   │   └── Bots/        # Gestor_Bots and Hypervisor
│   │   └── AWS/             # EC2 / S3 orchestration
│   ├── Services/            # Modular world generator and support services
│   ├── Utils/               # Utilities (geometry, files, sound…)
│   ├── DEV/                 # Test scenarios and example bot
│   ├── Tests/               # Test suite (pytest)
│   └── compile_protos.py    # Compiles the .proto files
└── unity/                   # Unity project (visualization client)
```

## Requirements

- **Python 3.11 or higher** (recommended)
- **Unity 6000.4** (only if you want to use the viewer)
- An AWS account (only for remote mode)

```bash
pip install grpcio grpcio-tools protobuf neat-python numpy scipy opensimplex \
            boto3 pyyaml psutil bitarray vectors requests pillow matplotlib \
            librosa pytest pytest-asyncio
```

## Getting started

Run all commands from the `python/` folder.

### 1. Compile the protobufs

The generated files are not committed to the repository, so they must be created once:

```bash
cd python
python compile_protos.py
```

### 2. Configure the environment

Copy or create a `.env.local` file with, at minimum, the import root:

```bash
PYTHONPATH=.
```

World parameters (`GRID_WIDTH`, `GRID_HEIGHT`, `SECTOR_SIZE`, `HABILITAR_BOTS`, `LOG_LEVEL`, `FRESH`…) are read from `Config/settings.py` and can be overridden with environment variables.

### 3. Run in local mode

Starts the whole system as subprocesses on your machine:

```bash
# Linux / macOS - Full game with bots
FRESH=true python Main.py --modo local
```

```powershell
# Windows (PowerShell) - Full game with bots
$env:FRESH="true"; python Main.py --modo local

# Windows (PowerShell) - Pure geophysical simulation (terrain, climate & hydrology, without bots)
$env:HABILITAR_BOTS="false"; $env:FRESH="true"; python Main.py --modo local
```

`FRESH=true` ignores saved snapshots and starts a new game (automatically generating world terrain and hydrology if they do not exist). To load a specific test scenario:

```bash
python Main.py --modo local --escenario <name>
```

Available scenarios are registered in `DEV/Escenarios/escenarios.py`.

### 4. Remote and production modes

```bash
python Main.py --modo remoto        # Launches the infrastructure on AWS (requires config.yaml)
python Main.py --modo produccion --componente sector --id sector_0_1 --sesion <id> --bucket <bucket>
```

Instance, network and timeout settings live in `Infraestructura/AWS/config.yaml`.

## Tests

```bash
cd python
pytest                    # whole suite
pytest -m unit            # pure tests, no network
pytest -m integration     # real components working together (in-process gRPC)
pytest -m e2e             # full stack as subprocesses
```

## Tech stack

Python · gRPC · Protocol Buffers · HyperNEAT / NEAT · NumPy · SciPy · asyncio · AWS (EC2, S3) · Unity (URP) · pytest

## License

<!-- TODO: pick a license (e.g. MIT) and add a LICENSE file. Without one, nobody is legally allowed to reuse your code. -->
