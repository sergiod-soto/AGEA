using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Sirenix.Serialization;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections.Concurrent;

public class ConexionMundo : MonoBehaviour, IConexionMundo
{
    // Implementación explícita de la propiedad requerida por la interfaz
    ConcurrentQueue<JObject> IConexionMundo.AccionesPendientes => accionesPendientes;
    ConcurrentQueue<string> IConexionMundo.MensajesPendientes => mensajesPendientes;

    TcpClient client;
    StreamReader reader;
    StreamWriter writer;
    Thread receiveThread;
    Thread sendThread;
    volatile bool running = true;

    public ConcurrentQueue<JObject> accionesPendientes = new();
    public ConcurrentQueue<string> mensajesPendientes = new();


    public MonoBehaviour Datos;

    public string address;
    public int PORT;



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

    void ConectarConPython()
    {
        var stream = client.GetStream();
        byte[] buffer = new byte[8388608];
        StringBuilder sb = new();


        while (true)
        {
            string json = RetrieveJSON(stream, buffer, sb);
            Debug.Log("JSON recibido de python: " + json);
            try
            {
                JObject data = JObject.Parse(json);
                accionesPendientes.Enqueue(data);
            }
            catch (JsonReaderException e)
            {
                Debug.Log("Error al parsear JSON: " + json);
                Debug.Log("Error: " + e);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }

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
                    Debug.Log("[CLIENTE] Enviado a Python: " + json);
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
    public void EnviarMensaje(string data)
    {
        mensajesPendientes.Enqueue(data);
    }

    string RetrieveJSON(NetworkStream stream, byte[] buffer, StringBuilder sb)
    {
        string json = "";
        try
        {
            int bytesRead = stream.Read(buffer, 0, buffer.Length);
            if (bytesRead == 0) return null; // conexión cerrada

            sb.Append(Encoding.UTF8.GetString(buffer, 0, bytesRead));
            string data = sb.ToString();

            int endIndex;
            while ((endIndex = data.IndexOf("<END>")) != -1)
            {
                json = data.Substring(0, endIndex);
                data = data.Substring(endIndex + 5); // quitar "<END>"

                // limpiar el buffer parcial
                sb.Clear();
                sb.Append(data);

                // limpiar basura o saltos de línea
                return json.Trim();

            }
        }
        catch (Exception e)
        {
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
