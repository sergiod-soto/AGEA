// Assets/Scripts/VistaFoco/TraductorMundo.cs
using ComunicacionRemota;
using Newtonsoft.Json;
using System.Text;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Única fuente visual: pinta el Tilemap a partir de
    /// ActualizacionFoco.representacion. El campo 'celdas' que existía
    /// antes en el proto se retiró por completo del lado Python (era
    /// redundante con 'representacion' y mandaba el elemento sin
    /// filtrar, más pesado) -- confirmado que Unity no necesita esos
    /// datos para nada aparte de pintar, así que no hay contrapartida
    /// que reponer aquí.
    /// </summary>
    public class TraductorMundo : MonoBehaviour
    {
        [SerializeField] private FocoStreamReceiver receptor;
        [SerializeField] private Tilemap tilemap;
        [SerializeField] private CatalogoElementos catalogo;

        private void OnEnable() => receptor.OnActualizacionRecibida += Pintar;
        private void OnDisable() => receptor.OnActualizacionRecibida -= Pintar;

        private void Pintar(ActualizacionFoco actualizacion)
        {
            if (!actualizacion.Ok || actualizacion.Representacion.IsEmpty) return;

            string json = Encoding.UTF8.GetString(actualizacion.Representacion.ToByteArray());
            var payload = JsonConvert.DeserializeObject<RepresentacionPayload>(json);
            if (payload?.Elementos == null) return;

            // Snapshot completo: se limpia y se repinta entero en cada
            // pulso, igual que ModeloCeldas -- coherente con que el
            // protocolo no manda deltas (decisión ya tomada en el lado
            // Infraestructura). Si el mundo crece mucho esto es lo
            // primero a optimizar (repintar solo lo que cambió respecto
            // al pulso anterior).
            tilemap.ClearAllTiles();

            foreach (var entrada in payload.Elementos)
            {
                var elemento = entrada.Elemento;
                if (elemento == null) continue;

                TileBase tile = catalogo.ObtenerTile(elemento.TipoElemento, elemento.Clase);
                if (tile == null)
                {
                    Debug.LogWarning($"[TraductorMundo] Sin tile para tipo='{elemento.TipoElemento}' clase='{elemento.Clase}' (catálogo cerrado: hay que darlo de alta a mano en CatalogoElementos)");
                    continue;
                }

                var posicionCelda = new Vector3Int(elemento.Casilla.X, elemento.Casilla.Y, 0);
                tilemap.SetTile(posicionCelda, tile);
            }
        }
    }
}