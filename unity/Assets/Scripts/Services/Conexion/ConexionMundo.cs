using Newtonsoft.Json.Linq;
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using System.Collections.Concurrent;

public class ConexionMundo : MonoBehaviour, IConexionMundo
{
    TcpClient client;
    NetworkStream stream;

    Thread receiveThread;
    Thread sendThread;

    CancellationTokenSource _cts;

    ConcurrentQueue<JObject> accionesPendientes;
    ConcurrentQueue<byte[]> mensajesPendientes;

    public string address;
    public int PORT;

    public event Action OnDesconectado;

    // ── Unity ──────────────────────────────────────────────────────────────────

    void Awake()
    {
        accionesPendientes = new();
        mensajesPendientes = new();
    }

    void OnApplicationQuit()
    {
        _cts?.Cancel();
        stream?.Close();
        client?.Close();
    }

    // ── API pública ────────────────────────────────────────────────────────────

    public void Arrancar()
    {
        try
        {
            _cts = new CancellationTokenSource();
            client = new TcpClient(address, PORT);
            stream = client.GetStream();

            receiveThread = new Thread(() => HiloRecepcion(_cts.Token)) { IsBackground = true };
            sendThread = new Thread(() => HiloEnvio(_cts.Token)) { IsBackground = true };
            receiveThread.Start();
            sendThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogException(e);
        }
    }

    /// <summary>Encola un mensaje para enviarlo a Python (se serializa a length-prefix).</summary>
    public void EnviarMensaje(string data)
    {
        byte[] payload = Encoding.UTF8.GetBytes(data);
        byte[] length = BitConverter.GetBytes(payload.Length); // 4 bytes little-endian
        byte[] mensaje = new byte[4 + payload.Length];
        Buffer.BlockCopy(length, 0, mensaje, 0, 4);
        Buffer.BlockCopy(payload, 0, mensaje, 4, payload.Length);
        mensajesPendientes.Enqueue(mensaje);
    }

    public ConcurrentQueue<JObject> GetAccionesPendientes() => accionesPendientes;

    // ── Hilo de recepción ──────────────────────────────────────────────────────

    void HiloRecepcion(CancellationToken token)
    {
        try
        {
            while (!token.IsCancellationRequested)
            {
                // Leer exactamente 4 bytes de longitud
                byte[] lenBuf = LeerExacto(4, token);
                if (lenBuf == null) break;

                int payloadLen = BitConverter.ToInt32(lenBuf, 0);

                // Leer exactamente payloadLen bytes
                byte[] payload = LeerExacto(payloadLen, token);
                if (payload == null) break;

                string mensaje = Encoding.UTF8.GetString(payload);

                try { accionesPendientes.Enqueue(JObject.Parse(mensaje)); }
                catch { Debug.LogWarning("[ConexionMundo] JSON inválido:\n" + mensaje); }
            }
        }
        catch (Exception e) when (!token.IsCancellationRequested)
        {
            Debug.LogException(e);
        }

        if (!token.IsCancellationRequested)
        {
            Debug.LogWarning("[ConexionMundo] Conexión perdida.");
            OnDesconectado?.Invoke();
        }
    }

    /// <summary>Lee exactamente <paramref name="n"/> bytes del stream. Devuelve null si se cierra la conexión.</summary>
    byte[] LeerExacto(int n, CancellationToken token)
    {
        byte[] buf = new byte[n];
        int leidos = 0;

        while (leidos < n && !token.IsCancellationRequested)
        {
            int r = stream.Read(buf, leidos, n - leidos);
            if (r == 0) return null; // conexión cerrada
            leidos += r;
        }

        return leidos == n ? buf : null;
    }

    // ── Hilo de envío ──────────────────────────────────────────────────────────

    void HiloEnvio(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            try
            {
                if (mensajesPendientes.TryDequeue(out byte[] mensaje))
                    stream.Write(mensaje, 0, mensaje.Length);
                else
                    Thread.Sleep(5);
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