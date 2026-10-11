// Assets/Scripts/Core/Logica/Foco/TraductorMundo.cs
using Assets.Scripts.Core.Entities.Elementos;
using Assets.Scripts.Core.Mundo.Datos;
using ComunicacionRemota;
using Newtonsoft.Json;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Única fuente visual: pinta el suelo en el Tilemap y los
    /// elementos como GameObjects instanciados, a partir de
    /// ActualizacionFoco.Representar.
    ///
    /// Los elementos no pueden ir en el Tilemap porque varios pueden
    /// solaparse en la misma casilla (distinta 'capa'), y un Tilemap
    /// solo admite una tile por celda. El suelo, en cambio, no se
    /// solapa nunca, así que se queda en el Tilemap como antes.
    ///
    /// Elementos: snapshot completo por pulso, igual que el suelo — se
    /// destruyen todos los GameObjects existentes y se instancian de
    /// nuevo según el payload actual. Esto ignora deliberadamente
    /// 'id_elemento' (sin seguimiento por identidad ni pooling); si el
    /// número de elementos por pantalla crece y el coste de
    /// Destroy/Instantiate constante se nota, este es el punto a
    /// revisar (pasar a diff por id + pool).
    /// </summary>
    public class TraductorMundo : MonoBehaviour
    {
        [SerializeField] private Tilemap tilemap;
        [SerializeField] private CatalogoElementos catalogoElementos;
        [SerializeField] private CatalogoPrefabsElementos catalogoPrefabs;

        // Todos los elementos instanciados cuelgan de aquí, para poder
        // borrarlos todos de golpe en cada pulso sin tocar el resto de
        // la escena. Es un GameObject vacío creado en la escena (no un
        // prefab): se arrastra su Transform aquí desde el Inspector.
        [SerializeField] private Transform contenedorElementos;

        private IFocoStream _receptor;

        // Awake (no OnEnable): ServiceLocator tiene DefaultExecutionOrder
        // -100, así que para cuando este Awake se ejecuta el registro ya
        // está poblado.
        private void Awake() => _receptor = ServiceLocator.Instance.Get<IFocoStream>();

        private void OnEnable() => _receptor.OnActualizacionRecibida += Pintar;
        private void OnDisable() => _receptor.OnActualizacionRecibida -= Pintar;

        private void Pintar(ActualizacionFoco actualizacion)
        {
            if (!actualizacion.Ok || actualizacion.Representar.IsEmpty) return;

            string json = Encoding.UTF8.GetString(actualizacion.Representar.ToByteArray());
            var payload = JsonConvert.DeserializeObject<RepresentarPayload>(json);
            if (payload == null) return;

            PintarSuelo(payload.Suelo);
            PintarElementos(payload.Elementos);
        }

        private void PintarSuelo(List<SueloConComportamientos> suelo)
        {
            // Snapshot completo: coherente con que el protocolo no
            // manda deltas.
            tilemap.ClearAllTiles();

            if (suelo == null) return;

            foreach (var entrada in suelo)
            {
                var elemento = entrada.Elemento;
                if (elemento == null) continue;

                TileBase tile = catalogoElementos.ObtenerTileSuelo(elemento.Clase);
                if (tile == null)
                {
                    Debug.LogWarning($"[TraductorMundo] Sin tile de suelo para clase='{elemento.Clase}'");
                    continue;
                }

                var posicionCelda = new Vector3Int(elemento.Casilla.X, elemento.Casilla.Y, 0);
                tilemap.SetTile(posicionCelda, tile);
            }
        }

        private void PintarElementos(List<ElementoConComportamientos> elementos)
        {
            // Destruir todo lo instanciado en el pulso anterior antes
            // de recrear (snapshot completo, sin diff por id).
            for (int i = contenedorElementos.childCount - 1; i >= 0; i--)
                Destroy(contenedorElementos.GetChild(i).gameObject);

            if (elementos == null) return;

            foreach (var entrada in elementos)
            {
                var elemento = entrada.Elemento;
                if (elemento == null) continue;

                GameObject prefab = catalogoPrefabs.ObtenerPrefab(elemento.Clase);
                if (prefab == null)
                {
                    Debug.LogWarning($"[TraductorMundo] Sin prefab para clase='{elemento.Clase}' (catálogo cerrado: hay que darlo de alta a mano en CatalogoPrefabsElementos)");
                    continue;
                }

                var posicionCelda = new Vector3Int(elemento.Casilla.X, elemento.Casilla.Y, 0);
                // Centro de la celda en mundo, no la esquina, para que
                // el elemento quede centrado visualmente sobre el suelo.
                Vector3 posicionMundo = tilemap.CellToWorld(posicionCelda) + (Vector3)(tilemap.cellSize * 0.5f);

                // Asunción: 'rotacion' viene en grados enteros, sobre
                // el eje Z (vista cenital/2D). Ajustar si el servidor
                // usa otra convención.
                Quaternion rotacion = Quaternion.Euler(0f, 0f, (float)elemento.Rotacion);

                var instancia = Instantiate(prefab, posicionMundo, rotacion, contenedorElementos);

                // Asunción: 'tamanho' es un factor de escala uniforme.
                if (elemento.Tamanho > 0)
                    instancia.transform.localScale = Vector3.one * elemento.Tamanho;

                // 'capa' se usa como orden de dibujado entre elementos
                // solapados en la misma casilla. Requiere que el
                // prefab tenga un SpriteRenderer en la raíz o en un
                // hijo directo; si no lo tiene, se ignora en silencio.
                var renderer = instancia.GetComponentInChildren<SpriteRenderer>();
                if (renderer != null)
                    renderer.sortingOrder = elemento.Capa;
            }
        }
    }
}