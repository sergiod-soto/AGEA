using ComunicacionRemota;
using Newtonsoft.Json.Linq;
using System.Threading.Tasks;

public interface IConexionMundo : IService
{
    Task<EjecutarResultado> EnviarMensaje(ComponenteDestino componente, string operacion, JObject payload);
}

public class EjecutarResultado
{
    public bool ok;
    public string error;
    public JObject payload; // null si la respuesta no traía payload
}