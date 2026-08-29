// Assets/Scripts/Core/Entities/Elementos/CatalogoPrefabsElementos.cs
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Assets.Scripts.Core.Entities.Elementos
{
    [CreateAssetMenu(fileName = "CatalogoPrefabsElementos", menuName = "Elementos/Catalogo de Prefabs de Elementos")]
    public class CatalogoPrefabsElementos : ScriptableObject
    {
        [Serializable]
        public struct Entrada
        {
            [Tooltip("Coincide con '__clase__' del JSON. Obligatorio.")]
            public string clase;

            public GameObject prefab;
        }

        private const string ClaveErrorClase = "Error";

        [SerializeField] private List<Entrada> entradas = new();

        private Dictionary<string, GameObject> _indice;

        private void ConstruirIndiceSiHaceFalta()
        {
            if (_indice != null) return;

            _indice = new Dictionary<string, GameObject>();

            foreach (var e in entradas)
            {
                if (string.IsNullOrEmpty(e.clase))
                {
                    Debug.LogError($"[CatalogoPrefabsElementos] Entrada incompleta (clase='{e.clase}'): se ignora.");
                    continue;
                }

                var clave = e.clase;

                if (_indice.ContainsKey(clave))
                {
                    Debug.LogError($"[CatalogoPrefabsElementos] Entrada duplicada para clase='{e.clase}'. Se mantiene la primera.");
                    continue;
                }

                _indice[clave] = e.prefab;
            }
        }

        public GameObject ObtenerPrefab(string clase)
        {
            ConstruirIndiceSiHaceFalta();

            if (!string.IsNullOrEmpty(clase)
                && _indice.TryGetValue(clase, out var prefab))
            {
                return prefab;
            }

            Debug.LogWarning($"[CatalogoPrefabsElementos] Sin prefab para clase='{clase}'. Usando prefab de error.");

            if (_indice.TryGetValue(ClaveErrorClase, out var prefabError))
                return prefabError;

            Debug.LogError("[CatalogoPrefabsElementos] No se encontró la entrada de error (\"Error\") en el catálogo. Revisa el .asset.");
            return null;
        }
    }
}