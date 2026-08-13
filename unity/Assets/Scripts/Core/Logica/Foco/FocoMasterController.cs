// Assets/Scripts/VistaFoco/FocoMasterController.cs
using Common; // namespace generado a partir de common.proto (package common) -- VERIFICAR contra el stub real
using ComunicacionRemota;
using Grpc.Core;
using System;
using System.Threading.Tasks;
using UnityEngine;

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

        [Tooltip("Comportamientos a incluir en la representación (mismo filtro que ConsultarRepresentacion).")]
        [SerializeField] private string[] incluir = Array.Empty<string>();

        [SerializeField] private string modo = "unity_debug";

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
                await GrpcConnectionManager.Instancia.Stub.ActualizarFocoAsync(request);
            }
            catch (RpcException ex)
            {
                Debug.LogWarning($"[FocoMasterController] ActualizarFoco falló: {ex.StatusCode}");
            }
        }

        /// <summary>
        /// Traduce el encuadre de la cámara ortográfica a coordenadas de
        /// grid, aplicando el factor de escala configurable.
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

            var min = new Position
            {
                X = Mathf.FloorToInt(minXMundo / unidadesPorCelda),
                Y = Mathf.FloorToInt(minYMundo / unidadesPorCelda),
            };
            var max = new Position
            {
                X = Mathf.CeilToInt(maxXMundo / unidadesPorCelda),
                Y = Mathf.CeilToInt(maxYMundo / unidadesPorCelda),
            };
            return (min, max);
        }
    }
}