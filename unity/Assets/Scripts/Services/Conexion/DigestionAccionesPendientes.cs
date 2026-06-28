using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using UnityEngine;

public class DigestionAccionesPendientes : MonoBehaviour, IProcesamientoEntradaConexion
{
    IConexionMundo conexionMundo;

    readonly Dictionary<string, Action<JObject>> handlers = new();

    void Awake()
    {
        conexionMundo = ServiceLocator.Instance.Get<IConexionMundo>();
    }

    void Update()
    {
        while (conexionMundo.GetAccionesPendientes().TryDequeue(out JObject json))
            DigerirEntrada(json);
    }

    // ── API pública ────────────────────────────────────────────────────────────

    public void DigerirEntrada(JObject json)
    {
        if (json == null) return;

        string peticion = json["peticion"]?.ToString();
        if (peticion == null)
        {
            Debug.LogWarning("[Digestion] Mensaje sin campo 'peticion':\n" + json);
            return;
        }

        if (handlers.TryGetValue(peticion, out var handler))
            handler(json);
        else
            Debug.LogWarning($"[Digestion] Tipo desconocido: '{peticion}'");
    }

    public void RegistrarHandler(string peticion, Action<JObject> handler)
    {
        if (handlers.ContainsKey(peticion))
            Debug.LogError($"[Digestion] Ya existe un handler para '{peticion}'.");
        else
            handlers[peticion] = handler;
    }

    public void EliminarHandler(string peticion) => handlers.Remove(peticion);
}