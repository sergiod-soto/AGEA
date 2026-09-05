// Assets/Scripts/Core/Logica/Foco/FocoStreamReceiver.cs
using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using UnityEngine;
using ComunicacionRemota;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Consume el stream compartido SuscribirseFoco en un hilo de fondo.
    /// IMPORTANTE: los callbacks de Grpc.Core llegan en threads del pool
    /// de gRPC, NO en el hilo principal de Unity -- por eso aquí solo se
    /// encola lo recibido (ConcurrentQueue). El consumo real, que es lo
    /// que puede tocar Tilemap/GameObjects, pasa siempre por Update().
    ///
    /// Reconexión: si el stream se corta (red, reinicio del servidor) se
    /// reintenta con backoff exponencial (decisión acordada) hasta
    /// reconectar o hasta que el componente se desactive/destruya.
    ///
    /// Se registra en ServiceLocator como IFocoStream -- quien necesite
    /// las actualizaciones (TraductorMundo, ModeloElementosGlobales) lo
    /// piden con ServiceLocator.Instance.Get&lt;IFocoStream&gt;() y se
    /// suscriben al evento, en vez de depender de una referencia de
    /// escena por SerializeField.
    /// </summary>
    public class FocoStreamReceiver : MonoBehaviour, IFocoStream
    {
        [Tooltip("Backoff inicial entre reintentos de reconexión, en segundos.")]
        [SerializeField] private float backoffInicialSegundos = 1f;

        [Tooltip("Backoff máximo entre reintentos, en segundos.")]
        [SerializeField] private float backoffMaximoSegundos = 30f;

        /// Evento en el hilo principal de Unity: quien pinte (TraductorMundo)
        /// o quien mantenga modelos no visuales (ModeloCeldas,
        /// ModeloElementosGlobales) se suscribe aquí.
        public event Action<ActualizacionFoco> OnActualizacionRecibida;

        private readonly ConcurrentQueue<ActualizacionFoco> _cola = new();
        private CancellationTokenSource _cts;
        private float _backoffActual;

        private void OnEnable()
        {
            _backoffActual = backoffInicialSegundos;
            _cts = new CancellationTokenSource();
            _ = EscucharConReconexionAsync(_cts.Token);
        }

        private void OnDisable()
        {
            _cts?.Cancel();
            _cts?.Dispose();
        }

        private async Task EscucharConReconexionAsync(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    await EscucharUnaVezAsync(token);
                    // Si vuelve sin excepción, el servidor cerró el stream
                    // limpiamente -- también se reintenta en ese caso.
                }
                catch (RpcException ex)
                {
                    Debug.LogWarning($"[FocoStreamReceiver] Stream caído ({ex.StatusCode}) - {ex.Status.Detail} - {ex}");
                }
                catch (OperationCanceledException)
                {
                    // Cancelación esperada al desactivar el componente: no es error.
                    break;
                }
                catch (Exception ex)
                {
                    Debug.LogError($"[FocoStreamReceiver] Error inesperado: {ex}");
                }

                if (token.IsCancellationRequested) break;

                try
                {
                    await Task.Delay(TimeSpan.FromSeconds(_backoffActual), token);
                }
                catch (OperationCanceledException)
                {
                    break;
                }

                // Backoff exponencial con techo, para no martillear al
                // servidor si está caído de verdad.
                _backoffActual = Mathf.Min(_backoffActual * 2f, backoffMaximoSegundos);
            }
        }

        private async Task EscucharUnaVezAsync(CancellationToken token)
        {
            var stub = ServiceLocator.Instance.Get<IConexionGrpc>().Stub;
            using var call = stub.SuscribirseFoco(new SuscribirseFocoRequest(), cancellationToken: token);

            bool primerMensajeDeEstaConexion = true;

            while (await call.ResponseStream.MoveNext(token))
            {
                if (primerMensajeDeEstaConexion)
                {
                    // La conexión demostró estar sana: resetear el backoff
                    // para el próximo corte que pueda pasar más adelante.
                    _backoffActual = backoffInicialSegundos;
                    primerMensajeDeEstaConexion = false;
                }

                // Solo se encola: nada de tocar la API de Unity desde aquí.
                _cola.Enqueue(call.ResponseStream.Current);
            }
        }

        private void Update()
        {
            // Vacía la cola en el hilo principal. Como mucho procesa lo
            // acumulado desde el último frame -- nunca bloquea esperando red.
            while (_cola.TryDequeue(out var actualizacion))
            {
                OnActualizacionRecibida?.Invoke(actualizacion);
            }
        }
    }
}