// Assets/Scripts/Core/Entities/Elementos/ElementoInstancia.cs
using Newtonsoft.Json.Linq;

/// <summary>
/// Dato puro (sin MonoBehaviour) de un elemento del mundo, deserializado
/// a partir de UN ítem de "representacion.elementos[]" (formato real
/// confirmado, no el de "transporte"/"guardado" que se usa para Cell).
/// Es la única fuente de verdad para cualquier tipo de elemento (Bot,
/// Piedra, Elemento_Test, etc.): sustituye a BotInfo, ElementoMundo y DatosBot.
///
/// Cada ítem de "elementos[]" viene como dos bloques separados:
///   "elemento": { tamanho, casilla, rotacion, __clase__, capa, id_elemento, tipo_elemento }
///   "comportamientos": { NombreComportamiento: {...datos...}, ... }
/// Se guardan ambos bloques, no se aplanan, para no perder esa distinción
/// que ya trae el propio formato.
/// </summary>
public class ElementoInstancia
{
    public int IdElemento { get; private set; }      // elemento.id_elemento
    public string Clase { get; private set; }         // elemento.__clase__
    public string TipoElemento { get; private set; }  // elemento.tipo_elemento
    public int Capa { get; private set; }              // elemento.capa
    public int Tamanho { get; private set; }            // elemento.tamanho
    public (int x, int y) Casilla { get; private set; } // elemento.casilla.{x,y}
    public float Rotacion { get; private set; }          // elemento.rotacion

    // Dict abierto: cada comportamiento (Peso, Color, Sonoro, ...) se
    // guarda como JObject crudo. ComportamientoHandlers decide qué hacer
    // con cada uno; los que no tengan handler se ignoran sin error.
    public JObject Comportamientos { get; private set; }

    // Último tick en el que este elemento apareció en un ActualizacionFoco.
    // Lo usa ElementoPool para el grace period (destruir tras N ticks ausente).
    public long UltimoTickVisto { get; set; }

    /// <summary>
    /// Construye una instancia a partir de UN ítem de "representacion.elementos[]"
    /// (el JObject que contiene las claves "elemento" y "comportamientos").
    /// </summary>
    public static ElementoInstancia DesdeJson(JObject item, long tickActual)
    {
        var elemento = (JObject)item["elemento"];
        var casillaJson = elemento["casilla"];

        return new ElementoInstancia
        {
            IdElemento = (int)elemento["id_elemento"],
            Clase = (string)elemento["__clase__"],
            TipoElemento = (string)elemento["tipo_elemento"],
            Capa = (int)elemento["capa"],
            Tamanho = (int)elemento["tamanho"],
            Casilla = ((int)casillaJson["x"], (int)casillaJson["y"]),
            Rotacion = (float)elemento["rotacion"],
            Comportamientos = (JObject)item["comportamientos"],
            UltimoTickVisto = tickActual
        };
    }
}