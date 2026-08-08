// Assets/Scripts/Core/Entities/Elementos/ElementoView.cs
using UnityEngine;

/// <summary>
/// Componente ligero que vive en el prefab instanciado de un elemento
/// (Bot, Piedra, lo que sea). No guarda datos propios más allá del id:
/// siempre se actualiza a partir del ElementoInstancia que le pasa el pool,
/// para que no haya dos copias del mismo dato desincronizándose.
///
/// Los handlers de ComportamientoHandlers son los que realmente tocan
/// transform, sprites, sonidos, etc. — esta clase solo expone el punto
/// de entrada y guarda el último dato aplicado por si algún handler
/// necesita comparar contra el estado anterior (ej. "solo reproducir
/// sonido si cambió tal campo").
/// </summary>
public class ElementoView : MonoBehaviour
{
    public int IdElemento { get; private set; }
    public string Clase { get; private set; }

    // Última instancia de datos aplicada. Público para que los handlers
    // puedan leer campos que no tengan un método propio en esta clase.
    public ElementoInstancia Datos { get; private set; }

    /// <summary>
    /// Llamado por ElementoPool justo después de instanciar el prefab
    /// (una sola vez, fija identidad) y también en cada actualización
    /// posterior del mismo elemento.
    /// </summary>
    public void Inicializar(ElementoInstancia datos)
    {
        IdElemento = datos.IdElemento;
        Clase = datos.Clase;
        Datos = datos;
    }

    /// <summary>
    /// Aplica una actualización de datos: mueve/rota el transform según
    /// CoordinateMapper y delega el resto (color, sonido, etc.) en
    /// ComportamientoHandlers. La posición/rotación se tratan aquí porque
    /// son comunes a TODO elemento, a diferencia de los comportamientos
    /// opcionales.
    /// </summary>
    public void Actualizar(ElementoInstancia nuevosDatos, CoordinateMapper mapper)
    {
        Datos = nuevosDatos;

        transform.position = mapper.CasillaAPosicion(nuevosDatos.Casilla);
        transform.rotation = Quaternion.Euler(0f, 0f, nuevosDatos.Rotacion);

        ComportamientoHandlers.AplicarTodos(this, nuevosDatos.Comportamientos);
    }
}