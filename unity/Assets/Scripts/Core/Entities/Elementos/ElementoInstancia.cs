// Assets/Scripts/Core/Entities/Elementos/ElementoInstancia.cs
using Newtonsoft.Json.Linq;

/// <summary>
/// Dato puro (sin MonoBehaviour) de un elemento del mundo tal como llega
/// en "representacion" (ver logica_mundo.py::consultar_representacion).
/// Es la ÚNICA fuente de verdad para cualquier tipo de elemento (Bot, Piedra, etc.):
/// sustituye a BotInfo, ElementoMundo y DatosBot.
///
/// No conoce nada de Unity a propósito: así el pool puede comparar/actualizar
/// estos datos sin depender de que exista ya un GameObject para ellos.
/// </summary>
public class ElementoInstancia
{
    // "__clase__" en el JSON -> usado por PrefabRegistry para elegir el prefab.
    public string Clase { get; private set; }

    // Identificador único y estable del elemento (id_elemento en el JSON).
    // Es la clave que usa ElementoPool para saber "esto ya existe" vs "esto es nuevo".
    public int IdElemento { get; private set; }

    public int Capa { get; private set; }
    public int Tamanho { get; private set; }
    public (int x, int y) Casilla { get; private set; }
    public float Rotacion { get; private set; }
    public bool ComportamientoActivo { get; private set; }

    // Diccionario abierto: cada comportamiento (Color, Destruible, Sonoro, ...)
    // se guarda como JObject crudo. ComportamientoHandlers decide qué hacer
    // con cada uno; los que no tengan handler simplemente se ignoran.
    // Esto evita tener que tocar esta clase cada vez que el simulador añade
    // un comportamiento nuevo.
    public JObject Comportamientos { get; private set; }

    // Último tick en el que este elemento apareció en un ActualizacionFoco.
    // Lo usa ElementoPool para el grace period (destruir tras N ticks ausente).
    public long UltimoTickVisto { get; set; }

    /// <summary>
    /// Construye una instancia a partir de un elemento de "representacion.elementos[]".
    /// No valida exhaustivamente el JSON: si faltase un campo obligatorio,
    /// preferimos que falle aquí de forma ruidosa (excepción) a que se
    /// propague un dato a medias hacia el pool o el render.
    /// </summary>
    public static ElementoInstancia DesdeJson(JObject json, long tickActual)
    {
        var casillaJson = json["casilla"];

        return new ElementoInstancia
        {
            Clase = (string)json["__clase__"],
            IdElemento = (int)json["id_elemento"],
            Capa = (int)json["capa"],
            Tamanho = (int)json["tamanho"],
            Casilla = ((int)casillaJson["x"], (int)casillaJson["y"]),
            Rotacion = (float)json["rotacion"],
            ComportamientoActivo = (bool)json["comportamiento_activo"],
            Comportamientos = (JObject)json["comportamientos"],
            UltimoTickVisto = tickActual
        };
    }
}