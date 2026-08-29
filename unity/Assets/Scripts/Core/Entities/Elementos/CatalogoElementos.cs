// Assets/Scripts/Core/Entities/Elementos/CatalogoElementos.cs
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Assets.Scripts.Core.Entities.Elementos
{
    [CreateAssetMenu(fileName = "CatalogoSuelos", menuName = "VistaFoco/Catalogo de Suelos")]
    public class CatalogoElementos : ScriptableObject
    {
        [Serializable]
        public struct EntradaElementoSimple
        {
            [Tooltip("Coincide con '__clase__' del JSON. Obligatorio.")]
            public string clase;

            public TileBase tile;
        }

        // Entrada específica para suelo: el JSON de suelo no trae
        // 'tipo_elemento', así que no tiene sentido forzarlo aquí. Se
        // indexa solo por clase.
        [Serializable]
        public struct EntradaSuelo
        {
            [Tooltip("Coincide con '__clase__' del JSON de suelo. Obligatorio.")]
            public string clase;

            public TileBase tile;
        }

        private const string ClaveErrorClase = "error";

        [SerializeField] private List<EntradaElementoSimple> entradasElementoSimple = new();
        [SerializeField] private List<EntradaSuelo> entradasSuelo = new();

        private Dictionary<string, TileBase> _indice;
        private Dictionary<string, TileBase> _indiceSuelo;

        private void ConstruirIndiceSiHaceFalta()
        {
            if (_indice != null) return;

            _indice = new Dictionary<string, TileBase>();

            foreach (var e in entradasElementoSimple)
            {
                if (string.IsNullOrEmpty(e.clase))
                {
                    Debug.LogError($"[CatalogoElementos] Entrada incompleta (clase='{e.clase}'). Esta entrada se ignora.");
                    continue;
                }

                var clave = (e.clase);

                if (_indice.ContainsKey(clave))
                {
                    Debug.LogError($"[CatalogoElementos] Entrada duplicada para clase='{e.clase}': " +
                                    "hay más de una fila en el catálogo con esta misma combinación. Se mantiene la primera encontrada.");
                    continue;
                }

                _indice[clave] = e.tile;
            }
        }

        private void ConstruirIndiceSueloSiHaceFalta()
        {
            if (_indiceSuelo != null) return;

            _indiceSuelo = new Dictionary<string, TileBase>();

            foreach (var e in entradasSuelo)
            {
                if (string.IsNullOrEmpty(e.clase))
                {
                    Debug.LogError("[CatalogoElementos] Entrada de suelo sin 'clase': se ignora.");
                    continue;
                }

                if (_indiceSuelo.ContainsKey(e.clase))
                {
                    Debug.LogError($"[CatalogoElementos] Entrada de suelo duplicada para clase='{e.clase}'. Se mantiene la primera.");
                    continue;
                }

                _indiceSuelo[e.clase] = e.tile;
            }
        }

        public TileBase ObtenerTile(string clase)
        {
            ConstruirIndiceSiHaceFalta();

            if (!string.IsNullOrEmpty(clase) && _indice.TryGetValue(clase, out var tile))
            {
                return tile;
            }

            Debug.LogWarning($"[CatalogoElementos] Sin tile para clase='{clase}'. Usando tile de error.");

            if (_indice.TryGetValue(ClaveErrorClase, out var tileError))
                return tileError;

            Debug.LogError("[CatalogoElementos] No se encontró la entrada de error (\"error\",\"error\") en el catálogo. Revisa el .asset.");
            return null;
        }

        // Igual que ObtenerTile pero para suelo: solo por clase, ya que
        // el suelo no trae tipo_elemento en el JSON.
        public TileBase ObtenerTileSuelo(string clase)
        {
            ConstruirIndiceSueloSiHaceFalta();

            if (!string.IsNullOrEmpty(clase) && _indiceSuelo.TryGetValue(clase, out var tile))
                return tile;

            Debug.LogWarning($"[CatalogoElementos] Sin tile de suelo para clase='{clase}'. Usando tile de error.");

            if (_indiceSuelo.TryGetValue(ClaveErrorClase, out var tileError))
                return tileError;

            Debug.LogError("[CatalogoElementos] No se encontró la entrada de error (\"error\") en entradasSuelo. Revisa el .asset.");
            return null;
        }
    }
}