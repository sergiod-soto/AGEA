// Assets/Scripts/VistaFoco/Dto/ElementoRepresentado.cs
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Forma completa del JSON dentro de ActualizacionFoco.representacion:
    /// { "modo": ..., "elementos": [ { "elemento": {...}, "comportamientos": {...} }, ... ] }
    /// </summary>
    public class RepresentacionPayload
    {
        [JsonProperty("modo")] public string Modo;
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

    public class PosicionXY
    {
        [JsonProperty("x")] public int X;
        [JsonProperty("y")] public int Y;
    }
}