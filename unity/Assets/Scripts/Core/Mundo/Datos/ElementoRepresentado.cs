// Assets/Scripts/VistaFoco/Dto/ElementoRepresentado.cs
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Assets.Scripts.Core.Mundo.Datos
{
    /// <summary>
    /// Forma completa del JSON dentro de ActualizacionFoco.Representar:
    /// { "modo": ..., "suelo": [...], "elementos": [ { "elemento": {...}, "comportamientos": {...} }, ... ] }
    /// </summary>
    public class RepresentarPayload
    {
        [JsonProperty("modo")] public string Modo;
        [JsonProperty("suelo")] public List<SueloConComportamientos> Suelo;
        [JsonProperty("elementos")] public List<ElementoConComportamientos> Elementos;
    }

    /// <summary>
    /// Cada entrada de 'elementos': el elemento en sí + sus comportamientos
    /// FILTRADOS por el 'incluir' que pidió el master en FocoRequest (no
    /// vienen todos, a diferencia de ElementoCelda).
    /// </summary>
    public class ElementoConComportamientos
    {
        [JsonProperty("elemento")] public ElementoRepresentado Elemento;

        /// Contenido variable según el comportamiento (Peso, Comportamiento_Test...);
        /// se deja como JObject genérico -- CatalogoElementos / quien lo consuma
        /// sabe qué campos leer de cada uno cuando haga falta.
        [JsonProperty("comportamientos")] public Dictionary<string, JObject> Comportamientos;
    }

    /// <summary>
    /// OJO: 'casilla' aquí es un objeto {x,y} -- distinto del formato
    /// [x,y] que usa ElementoCelda.cs para el mismo concepto. Son dos
    /// serializaciones distintas del lado Python, no un error de esta
    /// clase.
    /// </summary>
    public class ElementoRepresentado
    {
        [JsonProperty("tamanho")] public int Tamanho;
        [JsonProperty("casilla")] public PosicionXY Casilla;
        [JsonProperty("rotacion")] public int Rotacion;
        [JsonProperty("__clase__")] public string Clase;
        [JsonProperty("capa")] public int Capa;
        [JsonProperty("id_elemento")] public long IdElemento;
        [JsonProperty("tipo_elemento")] public string TipoElemento;
    }

    /// <summary>
    /// Cada entrada de 'suelo': mismo patrón que ElementoConComportamientos
    /// pero para casillas de suelo, que no traen tipo_elemento/rotacion/
    /// tamanho -- el suelo no rota ni se solapa, así que esos campos no
    /// existen del lado Python para este caso.
    /// </summary>
    public class SueloConComportamientos
    {
        [JsonProperty("elemento")] public ElementoSueloRepresentado Elemento;
        [JsonProperty("comportamientos")] public Dictionary<string, JObject> Comportamientos;
    }

    /// <summary>
    /// Forma reducida de un elemento de suelo. Deliberadamente NO
    /// hereda de ElementoRepresentado ni comparte esa clase: mezclar
    /// ambos habría dejado Tamanho/Rotacion/TipoElemento siempre a su
    /// valor por defecto para suelo, sin forma de distinguir "0 real"
    /// de "este campo no existe para este tipo".
    /// </summary>
    public class ElementoSueloRepresentado
    {
        [JsonProperty("casilla")] public PosicionXY Casilla;
        [JsonProperty("__clase__")] public string Clase;
        [JsonProperty("capa")] public int Capa;
        [JsonProperty("id_elemento")] public long IdElemento;
    }

    public class PosicionXY
    {
        [JsonProperty("x")] public int X;
        [JsonProperty("y")] public int Y;
    }
}