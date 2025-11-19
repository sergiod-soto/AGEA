using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class ServidorFalsoPython : MonoBehaviour
{
    private Thread serverThread;
    private TcpListener listener;
    private volatile bool serverRunning;
    private TcpClient currentClient;

    public String direccionIP;
    public int puerto;

    readonly string mensajePeriodico1 = @"
        {
          ""tipo"": ""actualizacion"",
          ""bots"": [
            {
              ""id"": 0,
              ""x"": 0,
              ""y"": 0,
              ""rotacion"": 0
            },
            {
              ""id"": 1,
              ""x"": 10,
              ""y"": 15,
              ""rotacion"": 0
            }
          ]
        }<END>";

    readonly string mensajePeriodico2 = @"
        {
          ""tipo"": ""actualizacion"",
          ""bots"": [
            {
              ""id"": 0,
              ""x"": 20,
              ""y"": 0,
              ""rotacion"": 0
            },
            {
              ""id"": 1,
              ""x"": 10,
              ""y"": 15,
              ""rotacion"": 0
            }
          ]
        }<END>";

    string mensajePeriodico;

    // Lanza el servidor en un hilo aparte. Seguro para llamar desde el hilo principal.
    public void Arrancar_Servidor_Falso()
    {
        mensajePeriodico = mensajePeriodico1;

        if (serverThread != null && serverThread.IsAlive)
        {
            Debug.Log("ServidorFalso: el servidor ya está en ejecución.");
            return;
        }

        serverRunning = true;
        serverThread = new Thread(ServerLoop)
        {
            IsBackground = true,
            Name = "ServidorFalsoThread"
        };
        serverThread.Start();
    }

    // Bucle principal del servidor (se ejecuta en el hilo background)
    private void ServerLoop()
    {
        try
        {
            listener = new TcpListener(IPAddress.Parse(direccionIP), puerto);
            listener.Start();
            Debug.Log($"Servidor FALSO escuchando en {direccionIP}:{puerto}...");

            while (serverRunning)
            {



                TcpClient client = null;
                try
                {
                    // AcceptTcpClient es bloqueante: si listener.Stop() es llamado al parar,
                    // lanzará SocketException y romperá el bucle.
                    client = listener.AcceptTcpClient();
                }
                #region
                catch (SocketException se)
                {
                    if (!serverRunning)
                        break;
                    Debug.LogError($"ServidorFalso: SocketException en AcceptTcpClient: {se.SocketErrorCode} - {se.Message}");
                    Thread.Sleep(100);
                    continue;
                }
                catch (ObjectDisposedException)
                {
                    if (!serverRunning) break;
                    Debug.LogError("ServidorFalso: listener disposed inesperadamente");
                    break;
                }
                #endregion

                if (client == null) continue;

                using (client)
                {
                    currentClient = client;
                    Debug.Log("Cliente conectado.");

                    var stream = client.GetStream();
                    byte[] buffer = new byte[1024];

                    // --- START: sender thread usando CancellationTokenSource ----------
                    using (var senderCts = new CancellationTokenSource())
                    {
                        var token = senderCts.Token;
                        Thread senderThread = new(() =>
                        {
                            try
                            {
                                while (serverRunning && !token.IsCancellationRequested)
                                {
                                    if (mensajePeriodico.Equals(mensajePeriodico1))
                                    {
                                        mensajePeriodico = mensajePeriodico2;
                                    }
                                    else
                                    {
                                        mensajePeriodico = mensajePeriodico1;
                                    }
                                    string periodic = mensajePeriodico;
                                    byte[] outB = Encoding.UTF8.GetBytes(periodic + "\n");

                                    try
                                    {
                                        stream.Write(outB, 0, outB.Length);
                                    }
                                    catch (Exception)
                                    {
                                        // Si falla la escritura, salgo y permito que la lectura detecte cierre
                                        break;
                                    }

                                    // Intervalo entre envíos
                                    Thread.Sleep(1000);
                                }
                            }
                            catch (Exception ex)
                            {
                                Debug.LogError($"ServidorFalso senderThread error: {ex}");
                            }
                        })
                        { IsBackground = true, Name = "ServidorFalsoSenderThread" };

                        senderThread.Start();
                        // --- END: sender thread ------------------------------------------

                        // Bucle de lectura desde el cliente (permanece en este hilo)
                        while (serverRunning)
                        {
                            int bytes = 0;
                            try
                            {
                                // stream.Read es bloqueante; si el cliente cierra la conexión devuelve 0
                                bytes = stream.Read(buffer, 0, buffer.Length);
                            }
                            catch (Exception)
                            {
                                // error de lectura -> salir del loop del cliente
                                break;
                            }

                            if (bytes == 0)
                                break;

                            string msg = Encoding.UTF8.GetString(buffer, 0, bytes);
                            Debug.Log("Recibido en python: " + msg);

                            // Respuesta puntual a lo que llegue por el cliente (opcional)
                            //string respuesta = "OK desde el servidor falso (eco)";
                            //byte[] outBytes = Encoding.UTF8.GetBytes(respuesta + "\n");
                            //try
                            //{
                            //    stream.Write(outBytes, 0, outBytes.Length);
                            //}
                            //catch (Exception)
                            //{
                            //    Debug.Log("Error al escribir la respuesta.");
                            //    break;
                            //}
                        }

                        // Parar y esperar al sender
                        try
                        {
                            senderCts.Cancel();
                            if (!senderThread.Join(500))
                            {
                                try { senderThread.Abort(); } catch { }
                            }
                        }
                        catch (Exception) { }
                    } // senderCts.Dispose() aquí

                    currentClient = null;
                    Debug.Log("Cliente desconectado.");
                }
            }
        }
        catch (Exception ex)
        {
            Debug.Log($"ServidorFalso: error en el servidor: {ex}");
        }
        finally
        {
            try { listener?.Stop(); } catch { }
            listener = null;
            serverRunning = false;
            currentClient = null;
            Debug.Log("ServidorFalso: servidor detenido.");
        }
    }

    // Parar el servidor de forma segura (puedes llamarlo desde el hilo principal)
    public void StopServer()
    {
        serverRunning = false;

        try { listener?.Stop(); } catch { }
        try { currentClient?.Close(); } catch { }

        if (serverThread != null && serverThread.IsAlive)
        {
            // Espera breve a que el hilo termine
            if (!serverThread.Join(500))
            {
                try { serverThread.Abort(); } catch { } // último recurso (obsoleto pero disponible en .NET Framework)
            }
        }

        serverThread = null;
    }

    private void OnDestroy()
    {
        StopServer();
    }
}