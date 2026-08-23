// Assets/Scripts/Core/Logica/Foco/CatalogoElementos.cs
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Assets.Scripts.Core.Entities.Elementos
{
    /// <summary>
    /// Catálogo CERRADO (decisión acordada): tipo_elemento/__clase__ -> Tile.
    /// Se actualiza a mano en este ScriptableObject cada vez que se añade
    /// un tipo nuevo en Python. A propósito NO hay tile "por defecto" ni
    /// mecanismo automático: un tipo sin dar de alta aquí falla de forma
    /// visible (log de aviso en TraductorMundo) en vez de pintarse con
    /// un sprite genérico que pase desapercibido y oculte el desajuste.
    /// </summary>
    [CreateAssetMenu(fileName = "CatalogoElementos", menuName = "VistaFoco/Catalogo de Elementos")]
    public class CatalogoElementos : ScriptableObject
    {
        [Serializable]
        public struct Entrada
        {
            [Tooltip("Coincide con '__clase__' del JSON. Se usa si 'tipoElemento' viene vacío.")]
            public string clase;

            [Tooltip("Coincide con 'tipo_elemento' del JSON. Tiene prioridad sobre 'clase' si ambos están rellenos.")]
            public string tipoElemento;

            public TileBase tile;
        }

        [SerializeField] private List<Entrada> entradas = new();

        private Dictionary<string, TileBase> _porTipo;
        private Dictionary<string, TileBase> _porClase;

        private void ConstruirIndiceSiHaceFalta()
        {
            if (_porTipo != null) return;

            _porTipo = new Dictionary<string, TileBase>();
            _porClase = new Dictionary<string, TileBase>();
            foreach (var e in entradas)
            {
                if (!string.IsNullOrEmpty(e.tipoElemento)) _porTipo[e.tipoElemento] = e.tile;
                if (!string.IsNullOrEmpty(e.clase)) _porClase[e.clase] = e.tile;
            }
        }

        public TileBase ObtenerTile(string tipoElemento, string clase)
        {
            ConstruirIndiceSiHaceFalta();

            if (!string.IsNullOrEmpty(tipoElemento) && _porTipo.TryGetValue(tipoElemento, out var t))
                return t;
            if (!string.IsNullOrEmpty(clase) && _porClase.TryGetValue(clase, out var c))
                return c;
            return null;
        }
    }
}