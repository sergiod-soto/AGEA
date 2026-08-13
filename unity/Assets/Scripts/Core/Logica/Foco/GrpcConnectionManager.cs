// Assets/Scripts/VistaFoco/GrpcConnectionManager.cs
using System;
using Grpc.Net.Client;
using UnityEngine;
using ComunicacionRemota;

namespace Assets.Scripts.Core.Logica.Foco
{
    /// <summary>
    /// Punto único de entrada al canal gRPC contra Comunicaciones_Remoto.
    /// Vive como singleton de escena porque el canal (y el stub que lo
    /// envuelve) debe sobrevivir mientras dure la conexión con
    /// Infraestructura -- no tiene sentido crear uno nuevo por componente
    /// que necesite hablar con el servidor.
    ///
    /// Usa Grpc.Net.Client (decisión acordada: solo target Editor/Desktop,
    /// sin plan de mobile/consolas por ahora). Si más adelante se añade
    /// una plataforma con soporte HTTP/2 poco fiable (IL2CPP en móvil,
    /// por ejemplo), habría que revisar si este cliente sigue siendo
    /// la opción correcta para esa plataforma en concreto.
    /// </summary>
    public class GrpcConnectionManager : MonoBehaviour
    {
        public static GrpcConnectionManager Instancia { get; private set; }

        [Tooltip("URL completa del servidor de Comunicaciones_Remoto, incluyendo esquema (http:// o https://).")]
        [SerializeField] private string direccionServidor = "http://localhost:50051";

        private GrpcChannel _canal;

        /// Stub compartido: todo el que necesite llamar a Ejecutar/ActualizarFoco/
        /// SuscribirseFoco lo obtiene de aquí en vez de crear su propio canal.
        public ComunicacionRemotaService.ComunicacionRemotaServiceClient Stub { get; private set; }

        private void Awake()
        {
            // Singleton simple: si ya existe una instancia (p.ej. al recargar
            // escena), esta copia se destruye para no duplicar el canal.
            if (Instancia != null && Instancia != this)
            {
                Destroy(gameObject);
                return;
            }
            Instancia = this;
            DontDestroyOnLoad(gameObject);

            Conectar();
        }

        private void Conectar()
        {
            // ASUME servidor local en texto plano (sin TLS), igual que la
            // decisión original con ChannelCredentials.Insecure de Grpc.Core.
            // Grpc.Net.Client por defecto exige HTTP/2 sobre TLS; este switch
            // habilita h2c (HTTP/2 sin cifrar) para desarrollo local. El día
            // que el servidor use TLS de verdad, hay que quitar este switch
            // y cambiar 'direccionServidor' a https://.
            AppContext.SetSwitch("System.Net.Http.SocketsHttpHandler.Http2UnencryptedSupport", true);

            _canal = GrpcChannel.ForAddress(direccionServidor);
            Stub = new ComunicacionRemotaService.ComunicacionRemotaServiceClient(_canal);
        }

        private void OnApplicationQuit()
        {
            // GrpcChannel no tiene ShutdownAsync (eso es API de Grpc.Core);
            // aquí el cierre es síncrono via Dispose().
            _canal?.Dispose();
        }
    }
}