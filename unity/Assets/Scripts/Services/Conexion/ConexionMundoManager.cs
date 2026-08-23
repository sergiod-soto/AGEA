// Assets/Scripts/Services/Conexion/ConexionMundoManager.cs

using ComunicacionRemota;
using Google.Protobuf;   // ByteString
using Grpc.Core;         // RpcException
using Newtonsoft.Json.Linq;
using System.Threading.Tasks;
using UnityEngine;

public class ConexionMundoManager : MonoBehaviour, IConexionMundo
{
    private IConexionGrpc _conexionGrpc;

    private void Awake()
    {
        // Se resuelve en Awake porque ServiceLocator registra todos los
        // MonoBehaviour de la escena al cargar; para cuando algo llame a
        // EnviarMensaje ya debe estar disponible.
        _conexionGrpc = ServiceLocator.Instance.Get<IConexionGrpc>();
    }

    public async Task<EjecutarResultado> EnviarMensaje(ComponenteDestino componente, string operacion, JObject payload)
    {
        // El payload viaja como bytes UTF8 de JSON, igual que 'state' en
        // ElementoGlobalState -- consistente con el resto del contrato.
        string json = payload?.ToString(Newtonsoft.Json.Formatting.None) ?? "{}";

        var request = new EjecutarRequest
        {
            Componente = componente,
            Operacion = operacion,
            Payload = ByteString.CopyFromUtf8(json)
        };

        try
        {
            EjecutarResponse response = await _conexionGrpc.Stub.EjecutarAsync(request);

            JObject responsePayload = response.Payload.IsEmpty
                ? null
                : JObject.Parse(response.Payload.ToStringUtf8());

            return new EjecutarResultado
            {
                ok = response.Ok,
                error = response.Error,
                payload = responsePayload
            };
        }
        catch (RpcException ex)
        {
            // Esto es un fallo de TRANSPORTE (servidor
            // caído, timeout, canal roto) -- no response.Ok=false,
            // que es un fallo LÓGICO que el propio servidor reporta controlado.
            return new EjecutarResultado { ok = false, error = ex.Message, payload = null };
        }
    }
}