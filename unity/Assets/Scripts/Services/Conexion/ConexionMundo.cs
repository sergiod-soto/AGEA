using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Sirenix.Serialization;
using System;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using System.Collections.Concurrent;

public class ConexionMundo : MonoBehaviour, IConexionMundo
{
    IProcesamientoEntradaConexion procesamientoEntrada;

    TcpClient client;
    StreamReader reader;
    StreamWriter writer;
    Thread receiveThread;
    Thread sendThread;

    ConcurrentQueue<JObject> accionesPendientes;
    ConcurrentQueue<string> mensajesPendientes;

    public string address;
    public int PORT;

    void Start()
    {
        procesamientoEntrada = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();

        accionesPendientes = new();
        mensajesPendientes = new();
    }


    public void Arrancar()
    {
        try
        {
            client = new TcpClient(address, PORT);
            var stream = client.GetStream();
            reader = new StreamReader(stream);
            writer = new StreamWriter(stream) { AutoFlush = true };

            receiveThread = new Thread(ConectarConPython);
            sendThread = new Thread(HiloEnvio);
            receiveThread.Start();
            sendThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogException(e);
        }
    }

    // --- HILO DE RECEPCIÓN ---
    //  pongo el mensaje recibido en la cola de acciones pendientes
    void ConectarConPython()
    {
        var stream = client.GetStream();
        byte[] buffer = new byte[18608];
        StringBuilder sb = new();

        while (true)
        {
            accionesPendientes.Enqueue(RetrieveJSON(stream, buffer, sb));
        }
    }

    void HiloEnvio()
    {
        while (true)
        {
            try
            {
                if (mensajesPendientes.TryDequeue(out string mensaje))
                {
                    string json = JsonConvert.SerializeObject(mensaje);
                    writer.WriteLine(json + "\n<END>\n");
                    writer.Flush();
                    //Debug.Log("[CLIENTE] Enviado a Python: " + json);
                }
                else
                {
                    Thread.Sleep(5); // evitar consumo de CPU
                }
            }
            catch (IOException)
            {
                Debug.LogWarning("[CLIENTE] Error de conexión al enviar.");
                Thread.Sleep(500);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Thread.Sleep(100);
            }
        }
    }

    // --- METODO SEGURO PARA ENVIAR DESDE UNITY ---
    // pongo el string en la cola de mensajes pendientes
    public void EnviarMensaje(string data)
    {
        mensajesPendientes.Enqueue(data);
    }

    JObject RetrieveJSON(NetworkStream stream, byte[] buffer, StringBuilder sb)
    {
        try
        {
            int bytesRead = stream.Read(buffer, 0, buffer.Length);
            if (bytesRead == 0) return null; // conexión cerrada

            sb.Append(Encoding.UTF8.GetString(buffer, 0, bytesRead));
            string data = sb.ToString();
            int endIndex;
            while ((endIndex = data.IndexOf("<END>")) != -1)
            {
                data = data[..endIndex];

                // limpiar el buffer parcial
                sb.Clear();
                sb.Append(data);

                // lo convierto a jobject
                try
                {
                    JObject objectJson = JObject.Parse(data);
                    return objectJson;
                }
                catch
                {
                    Debug.Log("Error pasando data a json");
                    return null;
                }
            }
        }
        catch (Exception e)
        {
            Debug.Log("Error al recibir JSON:");
            Debug.LogException(e);
            return null;
        }
        return null;
    }

    public ConcurrentQueue<JObject> GetAccionesPendientes()
    {
        return accionesPendientes;
    }

    public ConcurrentQueue<string> GetMensajesPendientes()
    {
        throw new NotImplementedException();
    }
    void OnApplicationQuit()
    {
        writer?.Close();
        reader?.Close();
        client?.Close();
        receiveThread?.Abort();
        sendThread?.Abort();
    }
}
