// Assets/Scripts/Core/Logica/Foco/PrefabRegistry.cs
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Mapeo "__clase__" (Piedra, Bot, ...) -> prefab a instanciar.
/// Es un ScriptableObject editable a mano en el Inspector: cuando el
/// simulador añada un tipo de elemento nuevo, se añade una entrada aquí
/// y se le asigna el prefab correspondiente, sin tocar código.
///
/// Deliberadamente NO se resuelve por convención de nombres/carpeta de
/// Resources: preferimos que sea explícito y visible en el Inspector,
/// para que un __clase__ sin prefab asignado dé un error claro en vez
/// de fallar en tiempo de ejecución por una carpeta mal nombrada.
/// </summary>
[CreateAssetMenu(fileName = "PrefabRegistry", menuName = "VistaFoco/PrefabRegistry")]
public class PrefabRegistry : ScriptableObject
{
    [System.Serializable]
    public class Entrada
    {
        public string Clase;
        public GameObject Prefab;
    }

    public List<Entrada> Entradas = new();

    // Diccionario construido en caliente a partir de Entradas, para
    // búsqueda O(1) en tiempo de ejecución sin recorrer la lista cada vez.
    Dictionary<string, GameObject> mapa;

    void OnEnable()
    {
        ConstruirMapa();
    }

    void ConstruirMapa()
    {
        mapa = new Dictionary<string, GameObject>();
        foreach (var entrada in Entradas)
        {
            if (string.IsNullOrEmpty(entrada.Clase) || entrada.Prefab == null)
                continue;

            if (mapa.ContainsKey(entrada.Clase))
            {
                Debug.LogError($"[PrefabRegistry] Clase duplicada: '{entrada.Clase}'.");
                continue;
            }

            mapa[entrada.Clase] = entrada.Prefab;
        }
    }

    /// <summary>
    /// Devuelve el prefab asociado a una clase, o null si no hay ninguno
    /// registrado (el llamante decide si eso es un error o simplemente
    /// se ignora ese elemento).
    /// </summary>
    public GameObject ObtenerPrefab(string clase)
    {
        if (mapa == null) ConstruirMapa();

        if (mapa.TryGetValue(clase, out var prefab))
            return prefab;

        Debug.LogWarning($"[PrefabRegistry] No hay prefab registrado para '{clase}'.");
        return null;
    }
}