// Assets/Scripts/Core/Logica/Foco/FocoMasterController.cs
using System;
using System.Threading.Tasks;
using Grpc.Core;
using UnityEngine;
using ComunicacionRemota;
using Common;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Rol de "master": manda ActualizarFoco a intervalo fijo, SIEMPRE,
    /// independientemente de si la cámara se movió (decisión acordada).
    /// La región enviada se calcula a partir del encuadre actual de la
    /// cámara y el factor de escala configurable unidades-Unity/celda
    /// (decisión acordada: la escala no es 1:1 fija).
    /// </summary>
    public class FocoMasterController : MonoBehaviour
    {
        [SerializeField] private Camera camaraMaster;

        [Tooltip("Cuántas unidades de Unity equivalen a 1 celda del grid.")]
        [SerializeField] private float unidadesPorCelda = 1f;

        [Tooltip("Cada cuánto se manda ActualizarFoco, en segundos.")]
        [SerializeField] private float intervaloSegundos = 0.5f;

        [Tooltip("Comportamientos a incluir en la representación (mismo filtro que ConsultarRepresentar).")]
        [SerializeField] private string[] incluir = Array.Empty<string>();

        [SerializeField] private string modo = "unity_debug";

        [Tooltip(
            "Nº de celdas de margen que se añaden por cada lado del " +
            "encuadre real de la cámara, para pedir de más y evitar " +
            "'popping' (que aparezcan/desaparezcan casillas de golpe al " +
            "mover la cámara) mientras llega la siguiente actualización. " +
            "NO corrige el desajuste real entre unidadesPorCelda y el " +
            "tamaño de celda del Tilemap -- solo da margen de tolerancia " +
            "a ese error mientras no se corrija de raíz."
        )]
        [SerializeField] private int margenCeldas = 2;

        private float _acumulado;

        private void Update()
        {
            _acumulado += Time.deltaTime;
            if (_acumulado < intervaloSegundos) return;
            _acumulado = 0f;

            EnviarFocoActual();
        }

        private void EnviarFocoActual()
        {
            var (min, max) = CalcularRegionVisible();

            var request = new FocoRequest
            {
                Min = min,
                Max = max,
                Modo = modo,
            };
            request.Incluir.AddRange(incluir);

            // Fire-and-forget: no se bloquea el frame de Unity esperando el
            // Ack. Si falla, se loguea -- el propio intervalo fijo hace de
            // reintento natural, así que no hace falta lógica extra aquí.
            _ = EnviarAsync(request);
        }

        private async Task EnviarAsync(FocoRequest request)
        {
            try
            {
                await ServiceLocator.Instance.Get<IConexionGrpc>().Stub.ActualizarFocoAsync(request);
            }
            catch (RpcException ex)
            {
                Debug.LogWarning($"[FocoMasterController] ActualizarFoco falló: {ex.StatusCode}");
            }
            catch (Exception ex)
            {
                // Cualquier otro fallo (ServiceLocator sin registrar, stub en mal
                // estado, etc.) no debe quedar como excepción no observada: si esto
                // pasa en silencio, parecería "no llegan datos" sin pista de por qué.
                Debug.LogError($"[FocoMasterController] Error inesperado enviando foco: {ex}");
            }
        }

        /// <summary>
        /// Traduce el encuadre de la cámara ortográfica a coordenadas de
        /// grid, aplicando el factor de escala configurable, y añade un
        /// margen fijo de <see cref="margenCeldas"/> celdas por cada lado.
        /// Asume cámara ortográfica (coherente con Tilemap 2D); si el
        /// proyecto llegara a usar perspectiva habría que revisar esto.
        /// </summary>
        private (Position min, Position max) CalcularRegionVisible()
        {
            float altoMundo = camaraMaster.orthographicSize * 2f;
            float anchoMundo = altoMundo * camaraMaster.aspect;

            Vector3 centro = camaraMaster.transform.position;

            float minXMundo = centro.x - anchoMundo / 2f;
            float maxXMundo = centro.x + anchoMundo / 2f;
            float minYMundo = centro.y - altoMundo / 2f;
            float maxYMundo = centro.y + altoMundo / 2f;

            // Margen en celdas de grid, no en unidades de Unity -- así el
            // margen pedido es exacto independientemente de la escala
            // (unidadesPorCelda) configurada.
            var min = new Position
            {
                X = Mathf.FloorToInt(minXMundo / unidadesPorCelda) - margenCeldas,
                Y = Mathf.FloorToInt(minYMundo / unidadesPorCelda) - margenCeldas,
            };
            var max = new Position
            {
                X = Mathf.CeilToInt(maxXMundo / unidadesPorCelda) + margenCeldas,
                Y = Mathf.CeilToInt(maxYMundo / unidadesPorCelda) + margenCeldas,
            };
            return (min, max);
        }
    }
}