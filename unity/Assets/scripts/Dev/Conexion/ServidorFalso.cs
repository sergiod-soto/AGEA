using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

public class ServidorFalso : MonoBehaviour
{
     public void Arrancar_Servidor_Falso()
    {
        int port = 5001; // Puerto del servidor falso
        var listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port);

        listener.Start();
        Console.WriteLine($"Servidor FALSO escuchando en el puerto {port}...");

        while (true)
        {
            TcpClient client = listener.AcceptTcpClient();
            Console.WriteLine("Cliente conectado.");

            var stream = client.GetStream();
            byte[] buffer = new byte[1024];

            while (true)
            {
                int bytes = 0;

                try
                {
                    bytes = stream.Read(buffer, 0, buffer.Length);
                }
                catch
                {
                    break;
                }

                if (bytes == 0)
                    break;

                string msg = Encoding.UTF8.GetString(buffer, 0, bytes);
                Console.WriteLine("Recibido: " + msg);

                // Aquí respondes lo que tú quieras
                string respuesta = "OK desde el servidor falso";
                byte[] outBytes = Encoding.UTF8.GetBytes(respuesta);
                stream.Write(outBytes, 0, outBytes.Length);
            }

            client.Close();
            Console.WriteLine("Cliente desconectado.");
        }
    }
}
