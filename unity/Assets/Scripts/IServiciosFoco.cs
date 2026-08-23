// Assets/Scripts/Core/Logica/Foco/IServiciosFoco.cs
using System;
using ComunicacionRemota;

/*
 *      Conexión gRPC contra Comunicaciones_Remoto. Sustituye al viejo
 *      IConexionMundo (TCP/IP) para el flujo de datos del mundo/Vista_Foco.
 *      Expone el stub compartido para quien necesite llamar RPCs
 *      directamente (FocoStreamReceiver, FocoMasterController).
 *
 *      Sin namespace, igual que el resto de interfaces IService del
 *      proyecto -- así no hace falta 'using VistaFoco;' en scripts como
 *      GameMain para pedirlas al ServiceLocator.
 */

public interface IFocoStream : IService
{
    event Action<ActualizacionFoco> OnActualizacionRecibida;
}