from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Elementos import Nodo


def _libreria():
    return Nodo(
        "_libreria",
        [
            Nodo.Eleccion(
                [
                    _libreriaNumerica,
                    _libreriaDatos,
                    _libreriaAprendizaje,
                    _libreriaPercepcion,
                    _libreriaLenguaje,
                    _libreriaInteraccion,
                    _libreriaSistema,
                    _libreriaSeguridad,
                ]
            )
        ],
    )


def _libreriaNumerica():
    return Nodo(
        "_libreriaNumerica",
        [
            Nodo.Eleccion(
                [
                    _libreriaNumpy,
                    _libreriaScipy,
                ]
            )
        ],
    )


def _libreriaNumpy():
    return Nodo(
        "_libreriaNumpy",
        [
            Nodo.Import(None, ["numpy"]),
            Nodo.Eleccion(
                [
                    _numpyAtributos,
                    _numpyFunciones,
                    _numpyFuncionalidades,
                ]
            ),
        ],
    )


def _libreriaScipy():
    return Nodo(
        "_libreriaScipy",
        [
            Nodo.Import(None, ["scipy"]),
            Nodo.Eleccion([_scipyFunciones, _scipyOptimizacion]),
        ],
    )


def _scipyFunciones():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_scipyFunciones",
        [
            Nodo.Eleccion(
                [
                    ["scipy.linalg.solve(", _argumentos, ")"],
                    ["scipy.linalg.det(", _argumentos, ")"],
                    ["scipy.linalg.norm(", _argumentos, ")"],
                    ["scipy.fft.fft(", _argumentos, ")"],
                    ["scipy.fft.ifft(", _argumentos, ")"],
                    ["scipy.integrate.quad(", _argumentos, ")"],
                    ["scipy.stats.norm.pdf(", _argumentos, ")"],
                    ["scipy.stats.ttest_ind(", _argumentos, ")"],
                ]
            )
        ],
    )


def _scipyOptimizacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_scipyOptimizacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = scipy.optimize.minimize(", _argumentos, ")\n"],
                    [_variable, " = scipy.optimize.root(", _argumentos, ")\n"],
                    [_variable, " = scipy.optimize.linprog(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _numpyAtributos():
    return Nodo(
        "_numpyAtributos",
        [
            Nodo.Eleccion(
                [
                    "np.pi",
                    "np.inf",
                    "np.nan",
                    "np.e",
                ]
            )
        ],
    )


def _numpyFunciones():
    return Nodo(
        "_numpyFunciones",
        [
            Nodo.Eleccion(
                [
                    _numpyFuncionesArray,
                    _numpyFuncionesOperacion,
                    _numpyFuncionesEstadistica,
                ]
            )
        ],
    )


def _numpyFuncionesArray():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_numpyFuncionesArray",
        [
            Nodo.Eleccion(
                [
                    ["np.array(", _argumentos, ")"],
                    ["np.zeros(", _argumentos, ")"],
                    ["np.ones(", _argumentos, ")"],
                    ["np.arange(", _argumentos, ")"],
                    ["np.linspace(", _argumentos, ")"],
                    ["np.reshape(", _argumentos, ")"],
                ]
            )
        ],
    )


def _numpyFuncionesOperacion():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_numpyFuncionesOperacion",
        [
            Nodo.Eleccion(
                [
                    ["np.dot(", _argumentos, ")"],
                    ["np.transpose(", _argumentos, ")"],
                    ["np.concatenate(", _argumentos, ")"],
                    ["np.linalg.inv(", _argumentos, ")"],
                    ["np.linalg.eigvals(", _argumentos, ")"],
                ]
            )
        ],
    )


def _numpyFuncionesEstadistica():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_numpyFuncionesEstadistica",
        [
            Nodo.Eleccion(
                [
                    ["np.mean(", _argumentos, ")"],
                    ["np.std(", _argumentos, ")"],
                    ["np.min(", _argumentos, ")"],
                    ["np.max(", _argumentos, ")"],
                    ["np.sum(", _argumentos, ")"],
                    ["np.median(", _argumentos, ")"],
                ]
            )
        ],
    )


def _numpyFuncionalidades():
    return Nodo(
        "_numpyFuncionalidades",
        [
            Nodo.Eleccion(
                [
                    _numpyNormalizacion,
                    _numpyProductoMatricial,
                    _numpyEstadisticaCompleta,
                ]
            )
        ],
    )


def _numpyNormalizacion():
    from Base_Gramatica import _variable

    return Nodo(
        "_numpyNormalizacion",
        [
            _variable,
            " = (",
            _variable,
            " - np.mean(",
            _variable,
            ")) / np.std(",
            _variable,
            ")\n",
        ],
    )


def _numpyProductoMatricial():
    from Base_Gramatica import _variable

    return Nodo(
        "_numpyProductoMatricial",
        [
            _variable,
            " = np.dot(",
            _variable,
            ", ",
            _variable,
            ".T)\n",
        ],
    )


def _numpyEstadisticaCompleta():
    from Base_Gramatica import _variable

    return Nodo(
        "_numpyEstadisticaCompleta",
        [
            _variable,
            ' = {"mean": np.mean(',
            _variable,
            '), "std": np.std(',
            _variable,
            '), "min": np.min(',
            _variable,
            '), "max": np.max(',
            _variable,
            ")}\n",
        ],
    )


def _libreriaDatos():
    return Nodo("_libreriaDatos", [Nodo.Eleccion([_libreriaPandas, _libreriaPolars])])


def _libreriaPandas():
    return Nodo(
        "_libreriaPandas",
        [
            Nodo.Import(None, ["pandas"]),
            Nodo.Eleccion([_pandasCreacion, _pandasOperacion, _pandasAgregacion]),
        ],
    )


def _pandasCreacion():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_pandasCreacion",
        [
            Nodo.Eleccion(
                [
                    ["pandas.DataFrame(", _argumentos, ")"],
                    ["pandas.Series(", _argumentos, ")"],
                    ["pandas.read_csv(", _argumentos, ")"],
                    ["pandas.read_json(", _argumentos, ")"],
                    ["pandas.read_excel(", _argumentos, ")"],
                ]
            )
        ],
    )


def _pandasOperacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pandasOperacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, ".dropna()\n"],
                    [_variable, ".fillna(", _argumentos, ")\n"],
                    [_variable, ".merge(", _argumentos, ")\n"],
                    [_variable, ".groupby(", _argumentos, ")\n"],
                    [_variable, ".sort_values(", _argumentos, ")\n"],
                    [_variable, ".rename(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _pandasAgregacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pandasAgregacion",
        [
            Nodo.Eleccion(
                [
                    [
                        _variable,
                        " = ",
                        _variable,
                        ".groupby(",
                        _argumentos,
                        ").mean()\n",
                    ],
                    [_variable, " = ", _variable, ".pivot_table(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".describe()\n"],
                ]
            )
        ],
    )


def _libreriaPolars():
    return Nodo(
        "_libreriaPolars",
        [
            Nodo.Import(None, ["polars"]),
            Nodo.Eleccion([_polarsCreacion, _polarsOperacion]),
        ],
    )


def _polarsCreacion():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_polarsCreacion",
        [
            Nodo.Eleccion(
                [
                    ["polars.DataFrame(", _argumentos, ")"],
                    ["polars.Series(", _argumentos, ")"],
                    ["polars.read_csv(", _argumentos, ")"],
                    ["polars.read_parquet(", _argumentos, ")"],
                ]
            )
        ],
    )


def _polarsOperacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_polarsOperacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, ".filter(", _argumentos, ")\n"],
                    [_variable, ".select(", _argumentos, ")\n"],
                    [_variable, ".with_columns(", _argumentos, ")\n"],
                    [
                        _variable,
                        ".group_by(",
                        _argumentos,
                        ").agg(",
                        _argumentos,
                        ")\n",
                    ],
                    [_variable, ".join(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaAprendizaje():
    return Nodo(
        "_libreriaAprendizaje",
        [Nodo.Eleccion([_libreriaSklearn, _libreriaKeras, _libreriaTorch])],
    )


def _libreriaSklearn():
    return Nodo(
        "_libreriaSklearn",
        [
            Nodo.Import(
                "sklearn.linear_model", ["LinearRegression", "LogisticRegression"]
            ),
            Nodo.Import("sklearn.tree", ["DecisionTreeClassifier"]),
            Nodo.Import(
                "sklearn.ensemble",
                ["RandomForestClassifier", "GradientBoostingClassifier"],
            ),
            Nodo.Import(
                "sklearn.model_selection", ["train_test_split", "cross_val_score"]
            ),
            Nodo.Import("sklearn.preprocessing", ["StandardScaler", "MinMaxScaler"]),
            Nodo.Import("sklearn.metrics", ["accuracy_score", "mean_squared_error"]),
            Nodo.Eleccion([_sklearnModelos, _sklearnPreprocesado, _sklearnEvaluacion]),
        ],
    )


def _sklearnModelos():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_sklearnModelos",
        [
            Nodo.Eleccion(
                [
                    [
                        _variable,
                        " = LinearRegression()\n",
                        _variable,
                        ".fit(",
                        _argumentos,
                        ")\n",
                    ],
                    [
                        _variable,
                        " = LogisticRegression()\n",
                        _variable,
                        ".fit(",
                        _argumentos,
                        ")\n",
                    ],
                    [
                        _variable,
                        " = DecisionTreeClassifier()\n",
                        _variable,
                        ".fit(",
                        _argumentos,
                        ")\n",
                    ],
                    [
                        _variable,
                        " = RandomForestClassifier()\n",
                        _variable,
                        ".fit(",
                        _argumentos,
                        ")\n",
                    ],
                    [
                        _variable,
                        " = GradientBoostingClassifier()\n",
                        _variable,
                        ".fit(",
                        _argumentos,
                        ")\n",
                    ],
                ]
            )
        ],
    )


def _sklearnPreprocesado():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_sklearnPreprocesado",
        [
            Nodo.Eleccion(
                [
                    [
                        _variable,
                        ", ",
                        _variable,
                        ", ",
                        _variable,
                        ", ",
                        _variable,
                        " = train_test_split(",
                        _argumentos,
                        ")\n",
                    ],
                    [
                        _variable,
                        " = StandardScaler().fit_transform(",
                        _argumentos,
                        ")\n",
                    ],
                    [_variable, " = MinMaxScaler().fit_transform(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _sklearnEvaluacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_sklearnEvaluacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = accuracy_score(", _argumentos, ")\n"],
                    [_variable, " = mean_squared_error(", _argumentos, ")\n"],
                    [_variable, " = cross_val_score(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaKeras():
    return Nodo(
        "_libreriaKeras",
        [
            Nodo.Import("keras", ["Sequential", "Model"]),
            Nodo.Import(
                "keras.layers", ["Dense", "Conv2D", "LSTM", "Dropout", "Flatten"]
            ),
            Nodo.Import("keras.optimizers", ["Adam", "SGD"]),
            Nodo.Eleccion([_kerasModelo, _kerasCapas, _kerasEntrenamiento]),
        ],
    )


def _kerasModelo():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_kerasModelo",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = Sequential()\n"],
                    [_variable, " = Model(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _kerasCapas():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_kerasCapas",
        [
            Nodo.Eleccion(
                [
                    [_variable, ".add(Dense(", _argumentos, "))\n"],
                    [_variable, ".add(Conv2D(", _argumentos, "))\n"],
                    [_variable, ".add(LSTM(", _argumentos, "))\n"],
                    [_variable, ".add(Dropout(", _argumentos, "))\n"],
                    [_variable, ".add(Flatten())\n"],
                ]
            )
        ],
    )


def _kerasEntrenamiento():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_kerasEntrenamiento",
        [
            Nodo.Eleccion(
                [
                    [_variable, ".compile(optimizer=Adam(), loss=", _argumentos, ")\n"],
                    [_variable, ".compile(optimizer=SGD(), loss=", _argumentos, ")\n"],
                    [_variable, ".fit(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".predict(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaTorch():
    return Nodo(
        "_libreriaTorch",
        [
            Nodo.Import(None, ["torch"]),
            Nodo.Import("torch", ["nn", "optim"]),
            Nodo.Eleccion([_torchTensores, _torchRed, _torchEntrenamiento]),
        ],
    )


def _torchTensores():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_torchTensores",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = torch.tensor(", _argumentos, ")\n"],
                    [_variable, " = torch.zeros(", _argumentos, ")\n"],
                    [_variable, " = torch.ones(", _argumentos, ")\n"],
                    [_variable, " = torch.randn(", _argumentos, ")\n"],
                    [_variable, " = torch.from_numpy(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _torchRed():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_torchRed",
        [
            Nodo.Eleccion(
                [
                    ["nn.Linear(", _argumentos, ")"],
                    ["nn.Conv2d(", _argumentos, ")"],
                    ["nn.LSTM(", _argumentos, ")"],
                    ["nn.ReLU()"],
                    ["nn.Sigmoid()"],
                    ["nn.Softmax(", _argumentos, ")"],
                    ["nn.Dropout(", _argumentos, ")"],
                ]
            )
        ],
    )


def _torchEntrenamiento():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_torchEntrenamiento",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = optim.Adam(", _argumentos, ")\n"],
                    [_variable, " = optim.SGD(", _argumentos, ")\n"],
                    [_variable, ".backward()\n"],
                    [_variable, ".step()\n"],
                    [_variable, ".zero_grad()\n"],
                ]
            )
        ],
    )


def _libreriaPercepcion():
    return Nodo(
        "_libreriaPercepcion", [Nodo.Eleccion([_libreriaOpencv, _libreriaPillow])]
    )


def _libreriaOpencv():
    return Nodo(
        "_libreriaOpencv",
        [
            Nodo.Import(None, ["cv2"]),
            Nodo.Eleccion([_opencvIO, _opencvTransformacion, _opencvDeteccion]),
        ],
    )


def _opencvIO():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_opencvIO",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = cv2.imread(", _argumentos, ")\n"],
                    ["cv2.imwrite(", _argumentos, ")\n"],
                    ["cv2.imshow(", _argumentos, ")\n"],
                    [_variable, " = cv2.VideoCapture(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _opencvTransformacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_opencvTransformacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = cv2.resize(", _argumentos, ")\n"],
                    [_variable, " = cv2.cvtColor(", _argumentos, ")\n"],
                    [_variable, " = cv2.GaussianBlur(", _argumentos, ")\n"],
                    [_variable, " = cv2.flip(", _argumentos, ")\n"],
                    [_variable, " = cv2.rotate(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _opencvDeteccion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_opencvDeteccion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = cv2.Canny(", _argumentos, ")\n"],
                    [_variable, " = cv2.findContours(", _argumentos, ")\n"],
                    [_variable, " = cv2.HoughLines(", _argumentos, ")\n"],
                    ["cv2.rectangle(", _argumentos, ")\n"],
                    ["cv2.circle(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaPillow():
    return Nodo(
        "_libreriaPillow",
        [
            Nodo.Import("PIL", ["Image", "ImageFilter", "ImageDraw"]),
            Nodo.Eleccion([_pillowIO, _pillowTransformacion]),
        ],
    )


def _pillowIO():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pillowIO",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = Image.open(", _argumentos, ")\n"],
                    [_variable, ".save(", _argumentos, ")\n"],
                    [_variable, " = Image.new(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _pillowTransformacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pillowTransformacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = ", _variable, ".resize(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".rotate(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".filter(ImageFilter.BLUR)\n"],
                    [_variable, " = ", _variable, ".convert(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".crop(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaLenguaje():
    return Nodo("_libreriaLenguaje", [Nodo.Eleccion([_libreriaNltk, _libreriaSpacy])])


def _libreriaNltk():
    return Nodo(
        "_libreriaNltk",
        [
            Nodo.Import(None, ["nltk"]),
            Nodo.Import("nltk.tokenize", ["word_tokenize", "sent_tokenize"]),
            Nodo.Import("nltk.corpus", ["stopwords"]),
            Nodo.Eleccion([_nltkTokenizacion, _nltkAnalisis]),
        ],
    )


def _nltkTokenizacion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_nltkTokenizacion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = word_tokenize(", _argumentos, ")\n"],
                    [_variable, " = sent_tokenize(", _argumentos, ")\n"],
                    [_variable, " = stopwords.words(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _nltkAnalisis():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_nltkAnalisis",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = nltk.pos_tag(", _argumentos, ")\n"],
                    [_variable, " = nltk.ne_chunk(", _argumentos, ")\n"],
                    [_variable, " = nltk.FreqDist(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaSpacy():
    return Nodo(
        "_libreriaSpacy",
        [
            Nodo.Import(None, ["spacy"]),
            Nodo.Eleccion([_spacyProcesado, _spacyEntidades]),
        ],
    )


def _spacyProcesado():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_spacyProcesado",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = spacy.load(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, "(", _argumentos, ")\n"],
                    [_variable, " = [token.text for token in ", _variable, "]\n"],
                    [_variable, " = [token.lemma_ for token in ", _variable, "]\n"],
                ]
            )
        ],
    )


def _spacyEntidades():
    from Base_Gramatica import _variable

    return Nodo(
        "_spacyEntidades",
        [
            Nodo.Eleccion(
                [
                    [
                        _variable,
                        " = [(ent.text, ent.label_) for ent in ",
                        _variable,
                        ".ents]\n",
                    ],
                    [
                        _variable,
                        " = [chunk.text for chunk in ",
                        _variable,
                        ".noun_chunks]\n",
                    ],
                ]
            )
        ],
    )


def _libreriaInteraccion():
    return Nodo(
        "_libreriaInteraccion",
        [Nodo.Eleccion([_libreriaFlask, _libreriaFastapi, _libreriaRequests])],
    )


def _libreriaFlask():
    return Nodo(
        "_libreriaFlask",
        [
            Nodo.Import("flask", ["Flask", "request", "jsonify", "render_template"]),
            Nodo.Eleccion([_flaskApp, _flaskRutas]),
        ],
    )


def _flaskApp():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_flaskApp",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = Flask(__name__)\n"],
                    [_variable, ".run(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _flaskRutas():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_flaskRutas",
        [
            Nodo.Eleccion(
                [
                    ["@", _variable, ".route(", _argumentos, ")\n"],
                    ["return jsonify(", _argumentos, ")\n"],
                    ["return render_template(", _argumentos, ")\n"],
                    [_variable, " = request.json\n"],
                    [_variable, " = request.args.get(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaFastapi():
    return Nodo(
        "_libreriaFastapi",
        [
            Nodo.Import("fastapi", ["FastAPI", "HTTPException"]),
            Nodo.Import("fastapi.responses", ["JSONResponse"]),
            Nodo.Eleccion([_fastapiApp, _fastapiRutas]),
        ],
    )


def _fastapiApp():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_fastapiApp",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = FastAPI()\n"],
                    ["raise HTTPException(status_code=", _argumentos, ")\n"],
                    ["return JSONResponse(content=", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _fastapiRutas():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_fastapiRutas",
        [
            Nodo.Eleccion(
                [
                    ["@", _variable, ".get(", _argumentos, ")\n"],
                    ["@", _variable, ".post(", _argumentos, ")\n"],
                    ["@", _variable, ".put(", _argumentos, ")\n"],
                    ["@", _variable, ".delete(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaRequests():
    return Nodo(
        "_libreriaRequests",
        [
            Nodo.Import(None, ["requests"]),
            Nodo.Eleccion([_requestsLlamadas, _requestsSesion]),
        ],
    )


def _requestsLlamadas():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_requestsLlamadas",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = requests.get(", _argumentos, ")\n"],
                    [_variable, " = requests.post(", _argumentos, ")\n"],
                    [_variable, " = requests.put(", _argumentos, ")\n"],
                    [_variable, " = requests.delete(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _requestsSesion():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_requestsSesion",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = requests.Session()\n"],
                    [_variable, ".headers.update(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".json()\n"],
                    [_variable, " = ", _variable, ".status_code\n"],
                ]
            )
        ],
    )


def _libreriaSistema():
    return Nodo(
        "_libreriaSistema",
        [Nodo.Eleccion([_libreriaPathlib, _libreriaSubprocess, _libreriaLogging])],
    )


def _libreriaPathlib():
    return Nodo(
        "_libreriaPathlib",
        [
            Nodo.Import("pathlib", ["Path"]),
            Nodo.Eleccion([_pathlibRutas, _pathlibOperaciones]),
        ],
    )


def _pathlibRutas():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pathlibRutas",
        [
            Nodo.Eleccion(
                [
                    [_variable, " = Path(", _argumentos, ")\n"],
                    [_variable, " = Path.cwd()\n"],
                    [_variable, " = Path.home()\n"],
                    [_variable, " = ", _variable, " / ", _argumentos, "\n"],
                ]
            )
        ],
    )


def _pathlibOperaciones():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_pathlibOperaciones",
        [
            Nodo.Eleccion(
                [
                    [_variable, ".mkdir(", _argumentos, ")\n"],
                    [_variable, ".unlink()\n"],
                    [_variable, ".rename(", _argumentos, ")\n"],
                    [_variable, " = ", _variable, ".read_text()\n"],
                    [_variable, ".write_text(", _argumentos, ")\n"],
                    [_variable, " = list(", _variable, ".glob(", _argumentos, "))\n"],
                ]
            )
        ],
    )


def _libreriaSubprocess():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_libreriaSubprocess",
        [
            Nodo.Import(None, ["subprocess"]),
            Nodo.Eleccion(
                [
                    [
                        _variable,
                        " = subprocess.run(",
                        _argumentos,
                        ", capture_output=True)\n",
                    ],
                    [_variable, " = subprocess.Popen(", _argumentos, ")\n"],
                    [_variable, " = subprocess.check_output(", _argumentos, ")\n"],
                ]
            ),
        ],
    )


def _libreriaLogging():
    return Nodo(
        "_libreriaLogging",
        [Nodo.Import(None, ["logging"]), Nodo.Eleccion([_loggingConfig, _loggingUso])],
    )


def _loggingConfig():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_loggingConfig",
        [
            Nodo.Eleccion(
                [
                    ["logging.basicConfig(level=logging.DEBUG)\n"],
                    ["logging.basicConfig(level=logging.INFO)\n"],
                    [_variable, " = logging.getLogger(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _loggingUso():
    from Base_Gramatica import _argumentos

    return Nodo(
        "_loggingUso",
        [
            Nodo.Eleccion(
                [
                    ["logging.debug(", _argumentos, ")\n"],
                    ["logging.info(", _argumentos, ")\n"],
                    ["logging.warning(", _argumentos, ")\n"],
                    ["logging.error(", _argumentos, ")\n"],
                ]
            )
        ],
    )


def _libreriaSeguridad():
    return Nodo(
        "_libreriaSeguridad",
        [Nodo.Eleccion([_libreriaHashlib, _libreriaSecrets, _libreriaJwt])],
    )


def _libreriaHashlib():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_libreriaHashlib",
        [
            Nodo.Import(None, ["hashlib"]),
            Nodo.Eleccion(
                [
                    [_variable, " = hashlib.sha256(", _argumentos, ").hexdigest()\n"],
                    [_variable, " = hashlib.md5(", _argumentos, ").hexdigest()\n"],
                    [_variable, " = hashlib.sha512(", _argumentos, ").hexdigest()\n"],
                    [_variable, " = hashlib.blake2b(", _argumentos, ").hexdigest()\n"],
                ]
            ),
        ],
    )


def _libreriaSecrets():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_libreriaSecrets",
        [
            Nodo.Import(None, ["secrets"]),
            Nodo.Eleccion(
                [
                    [_variable, " = secrets.token_hex(", _argumentos, ")\n"],
                    [_variable, " = secrets.token_bytes(", _argumentos, ")\n"],
                    [_variable, " = secrets.token_urlsafe(", _argumentos, ")\n"],
                    [_variable, " = secrets.choice(", _argumentos, ")\n"],
                ]
            ),
        ],
    )


def _libreriaJwt():
    from Base_Gramatica import _argumentos, _variable

    return Nodo(
        "_libreriaJwt",
        [
            Nodo.Import("jwt", ["encode", "decode"]),
            Nodo.Eleccion(
                [
                    [_variable, " = encode(", _argumentos, ")\n"],
                    [_variable, " = decode(", _argumentos, ")\n"],
                ]
            ),
        ],
    )
