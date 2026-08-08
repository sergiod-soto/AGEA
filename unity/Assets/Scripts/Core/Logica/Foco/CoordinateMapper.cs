// Assets/Scripts/Core/Logica/Foco/CoordinateMapper.cs
using UnityEngine;

/// <summary>
/// Traduce entre la rejilla lógica del mundo simulado (enteros x,y) y
/// posiciones reales en Unity. Es la única pieza que sabe la fórmula
/// (posición = casilla * tamaño de casilla) — si el día de mañana cambia
/// la orientación de ejes o el origen, se toca solo aquí.
/// </summary>
public class CoordinateMapper
{
    readonly float tamanoCasilla;

    public CoordinateMapper(FocoSettings settings)
    {
        tamanoCasilla = settings.TamanoCasilla;
    }

    /// <summary>
    /// (x, y) lógico -> Vector3 Unity. Z se deja en 0 porque la celda es
    /// invisible en 2D y no hay profundidad real que representar aquí;
    /// si algún prefab necesita un Z concreto (para orden de dibujado, etc.)
    /// se ajusta en su propio handler, no en este mapeo genérico.
    /// </summary>
    public Vector3 CasillaAPosicion((int x, int y) casilla)
    {
        return new Vector3(casilla.x * tamanoCasilla, casilla.y * tamanoCasilla, 0f);
    }
}