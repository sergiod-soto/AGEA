using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using System.Collections.Concurrent;

public class ConexionMundo : MonoBehaviour, IConexionMundo
{
    IProcesamientoEntradaConexion procesamientoEntrada;

    TcpClient client;
    NetworkStream stream;
    System.IO.StreamWriter writer;

    Thread receiveThread;
    Thread sendThread;

    CancellationTokenSource _cts;

    ConcurrentQueue<JObject> accionesPendientes;
    ConcurrentQueue<string> mensajesPendientes;

    public string address;
    public int PORT;

    // ── Unity ─────────────────────────────────────────────────────────────────

    void Awake()
    {
        procesamientoEntrada = ServiceLocator.Instance.Get<IProcesamientoEntradaConexion>();
        accionesPendientes = new();
        mensajesPendientes = new();
    }

    void OnApplicationQuit()
    {
        _cts?.Cancel();
        writer?.Close();
        stream?.Close();
        client?.Close();
    }

    // ── API pública ───────────────────────────────────────────────────────────

    public void Arrancar()
    {
        try
        {
            _cts = new CancellationTokenSource();
            client = new TcpClient(address, PORT);
            stream = client.GetStream();
            writer = new System.IO.StreamWriter(stream) { AutoFlush = true };

            receiveThread = new Thread(() => HiloRecepcion(_cts.Token));
            sendThread = new Thread(() => HiloEnvio(_cts.Token));
            receiveThread.IsBackground = true;
            sendThread.IsBackground = true;
            receiveThread.Start();
            sendThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogException(e);
        }
    }

    /// <summary>Encola un mensaje para enviarlo a Python.</summary>
    public void EnviarMensaje(string data)
    {
        mensajesPendientes.Enqueue(data + "<END>");
    }

    public ConcurrentQueue<JObject> GetAccionesPendientes() => accionesPendientes;
    public ConcurrentQueue<string> GetMensajesPendientes() => mensajesPendientes;

    // ── Hilo de recepción ─────────────────────────────────────────────────────

    void HiloRecepcion(CancellationToken token)
    {
        byte[] buffer = new byte[4096];
        StringBuilder sb = new();

        while (!token.IsCancellationRequested)
        {
            try
            {
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) break; // conexión cerrada

                sb.Append(Encoding.UTF8.GetString(buffer, 0, bytesRead));

                // Procesar TODOS los mensajes completos que hayan llegado
                // en este read (puede haber más de uno)
                ProcesarMensajesEnBuffer(sb);
            }
            catch (Exception e) when (!token.IsCancellationRequested)
            {
                Debug.Log("[ConexionMundo] Error al recibir:");
                Debug.LogException(e);
            }
        }
    }

    void ProcesarMensajesEnBuffer(StringBuilder sb)
    {
        const string FIN = "<END>";

        string data = sb.ToString();
        int endIndex;

        while ((endIndex = data.IndexOf(FIN)) != -1)
        {
            string mensaje = data[..endIndex];
            string resto = data[(endIndex + FIN.Length)..];

            // Actualizar el buffer con lo que queda tras el <END>
            sb.Clear();
            sb.Append(resto);
            data = resto;

            if (string.IsNullOrWhiteSpace(mensaje)) continue;

            try
            {
                accionesPendientes.Enqueue(JObject.Parse(mensaje));
            }
            catch
            {
                Debug.Log("[ConexionMundo] Error parseando JSON:\n" + mensaje);
            }
        }
    }

    // ── Hilo de envío ─────────────────────────────────────────────────────────

    void HiloEnvio(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            try
            {
                if (mensajesPendientes.TryDequeue(out string mensaje))
                {
                    writer.WriteLine(mensaje);
                }
                else
                {
                    Thread.Sleep(5);
                }
            }
            catch (System.IO.IOException)
            {
                Debug.LogWarning("[ConexionMundo] Error de conexión al enviar.");
                Thread.Sleep(500);
            }
            catch (Exception e) when (!token.IsCancellationRequested)
            {
                Debug.LogException(e);
                Thread.Sleep(100);
            }
        }
    }
}