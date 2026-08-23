// Interfaz global, sin namespace -- mismo patrón que el resto de IService.
// Expone el stub ya conectado para que otros scripts (FocoStreamReceiver,
// ConexionMundoManager, etc.) lo pidan vía ServiceLocator sin abrir su
// propio canal.
using ComunicacionRemota;

public interface IConexionGrpc : IService
{
    ComunicacionRemotaService.ComunicacionRemotaServiceClient Stub { get; }
}