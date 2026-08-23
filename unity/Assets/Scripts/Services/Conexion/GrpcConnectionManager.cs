// Assets/Scripts/Services/Conexion/GrpcConnectionManager.cs
using System;
using Cysharp.Net.Http;   // YetAnotherHttpHandler
using Grpc.Net.Client;
using UnityEngine;
using ComunicacionRemota;

namespace Assets.Scripts.Services.Conexion
{
    /// <summary>
    /// Servicio de conexión gRPC contra Comunicaciones_Remoto. Canal
    /// GENÉRICO y compartido: no es específico de Foco -- lo consumen
    /// tanto FocoStreamReceiver (Foco) como ConexionMundoManager
    /// (bots/mundo, vía Ejecutar). Por eso vive en Services/Conexion y
    /// no en Core/Logica/Foco.
    ///
    /// Se registra en ServiceLocator como IConexionGrpc; quien necesite
    /// el stub lo pide con ServiceLocator.Instance.Get&lt;IConexionGrpc&gt;()
    /// en vez de un singleton propio.
    ///
    /// Usa Grpc.Net.Client (decisión acordada: solo target Editor/Desktop).
    ///
    /// IMPORTANTE — handler HTTP: en Mono (Editor/Desktop), HttpClient no
    /// tiene una implementación real de SocketsHttpHandler, y cae en
    /// MonoWebRequestHandler, que no soporta lectura progresiva de un
    /// stream HTTP/2 de duración indefinida. Esto rompe el RPC de
    /// streaming (SuscribirseFoco) con StatusCode=Internal, aunque los
    /// RPC unarios (Ejecutar, ActualizarFoco, Heartbeat) funcionen bien
    /// sobre ese mismo handler. YetAnotherHttpHandler (Cysharp) es un
    /// handler HTTP/2 nativo que sí soporta streaming, y funciona igual
    /// en Mono e IL2CPP -- por eso se fuerza explícitamente en vez de
    /// dejar que GrpcChannel.ForAddress elija el handler por defecto.
    /// </summary>
    public class GrpcConnectionManager : MonoBehaviour, IConexionGrpc
    {
        [Tooltip("URL completa del servidor de Comunicaciones_Remoto, incluyendo esquema (http:// o https://).")]
        [SerializeField] private string direccionServidor = "http://localhost:50500";

        private GrpcChannel _canal;
        private YetAnotherHttpHandler _httpHandler;

        public ComunicacionRemotaService.ComunicacionRemotaServiceClient Stub { get; private set; }

        private void Awake()
        {
            Conectar();
        }

        private void Conectar()
        {
            // Ya no hace falta el switch de Http2UnencryptedSupport ni el
            // AppContext.SetSwitch: YetAnotherHttpHandler gestiona h2c
            // (HTTP/2 sin TLS) directamente en sus opciones.
            _httpHandler = new YetAnotherHttpHandler
            {
                Http2Only = true, // el servidor solo habla HTTP/2 en texto plano (h2c)
            };

            _canal = GrpcChannel.ForAddress(direccionServidor, new GrpcChannelOptions
            {
                HttpHandler = _httpHandler,
                // DisposeHttpClient=true por defecto ya libera _httpHandler
                // al hacer Dispose() del canal, pero lo mantenemos como
                // referencia propia para poder liberarlo explícitamente
                // si Dispose() del canal cambiase de comportamiento.
            });

            Stub = new ComunicacionRemotaService.ComunicacionRemotaServiceClient(_canal);
        }

        private void OnApplicationQuit()
        {
            _canal?.Dispose();
            _httpHandler?.Dispose();
        }
    }
}