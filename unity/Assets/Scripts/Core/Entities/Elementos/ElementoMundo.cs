/// <summary>
/// Clase base para los datos de cualquier elemento clicable del mundo.
/// Cada tipo de elemento tiene su propia subclase con sus stats.
///
/// Vive en: Core/Entities
///
/// Para añadir un nuevo tipo de elemento:
///   1. Crea una clase que herede de ElementoMundo (ej: DatosObstaculo)
///   2. Añade los campos que necesites
///   3. Crea su OverlayBase correspondiente
/// </summary>
public abstract class ElementoMundo { }


// ── Tipos concretos ───────────────────────────────────────────────────────────

public class DatosBot : ElementoMundo
{
    public int Id { get; set; }
    public int Generacion { get; set; }
    public bool EstaVivo { get; set; }

    // Ampliar aquí cuando la IA tenga más datos relevantes
    // public float[] PesosRed  { get; set; }
}
