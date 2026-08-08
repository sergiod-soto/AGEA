// Assets/Scripts/Core/Logica/Foco/FocoSettings.cs
using UnityEngine;

/// <summary>
/// Configuración de Vista_Foco editable desde el Inspector, sin tocar código.
/// Se crea como asset (Assets > Create > VistaFoco > FocoSettings) y se
/// asigna a los MonoBehaviour que la necesiten (ElementoPool, FocoMaster,
/// ComunicacionRemotaClient).
/// </summary>
[CreateAssetMenu(fileName = "FocoSettings", menuName = "VistaFoco/FocoSettings")]
public class FocoSettings : ScriptableObject
{
    [Header("Conexión")]
    [Tooltip("Dirección del servidor gRPC de Comunicaciones_Remoto, ej: http://localhost:50051")]
    public string ServerAddress = "http://localhost:50051";

    [Header("Mapa")]
    [Tooltip("Tamaño en unidades Unity de una casilla lógica. Posición = (x,y) * TamanoCasilla.")]
    public float TamanoCasilla = 1f;

    [Header("Pool de elementos")]
    [Tooltip("Ticks que un elemento puede estar ausente del foco antes de destruirse. " +
             "Pensado para tolerar que la cámara se mueva y vuelva sin recrear todo.")]
    public int TicksGraciaAntesDeDestruir = 5;

    [Header("Master (cámara)")]
    [Tooltip("Margen extra (en casillas) alrededor del viewport al calcular la región del foco, " +
             "para no pedir un ActualizarFoco por cada pequeño desplazamiento de cámara.")]
    public float MargenRegion = 2f;
}