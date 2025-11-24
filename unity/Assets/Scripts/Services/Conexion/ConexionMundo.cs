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

    // Implementación explícita de la propiedad requerida por la interfaz
    ConcurrentQueue<JObject> IConexionMundo.AccionesPendientes => accionesPendientes;
    ConcurrentQueue<string> IConexionMundo.MensajesPendientes => mensajesPendientes;

    TcpClient client;
    StreamReader reader;
    StreamWriter writer;
    Thread receiveThread;
    Thread sendThread;
    private volatile bool running = true;

    public ConcurrentQueue<JObject> accionesPendientes = new();
    public ConcurrentQueue<string> mensajesPendientes = new();

    public string address;
    public int PORT;

    void Start()
    {
        procesamientoEntrada = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();
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
        byte[] buffer = new byte[8388608];
        StringBuilder sb = new();

        while (true)
        {
            string jsonEntrada = RetrieveJSON(stream, buffer, sb);
            accionesPendientes.Enqueue(jsonEntrada);
        }
    }

    void HiloEnvio()
    {
        while (running)
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

    // --- MÉTODO SEGURO PARA ENVIAR DESDE UNITY ---
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
                string json = data[..endIndex];
                data = data[(endIndex + 5)..]; // quitar "<END>"

                // limpiar el buffer parcial
                sb.Clear();
                sb.Append(data);

                // limpiar basura o saltos de línea
                json = json.Trim();

                // lo pasamos a json
                return JObject.Parse(json);

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



    void OnApplicationQuit()
    {
        writer?.Close();
        reader?.Close();
        client?.Close();
        receiveThread?.Abort();
        sendThread?.Abort();
    }
}
