// Assets/Scripts/Core/Logica/Game/GameMain.cs
using UnityEngine;

/// <summary>
/// El flujo que había aquí antes -- leer JObject de
/// IConexionMundo.GetAccionesPendientes(), pasarlo por
/// IProcesamientoEntradaConexion.DigerirEntrada() y pintar bots con
/// IBotsLogica.RenderizarBots() -- se retira por completo: confirmado
/// que esos tres pasos solo existían para pintar, y ese camino ahora
/// es gRPC + TraductorMundo, que pinta el Tilemap suscribiéndose
/// directamente a IFocoStream (ver TraductorMundo.cs /
/// ModeloElementosGlobales.cs). GameMain ya no necesita mediar en ese
/// flujo -- TraductorMundo y ModeloElementosGlobales se resuelven solos
/// contra ServiceLocator.
///
/// Dejo la clase vacía en vez de borrar el fichero, por si tenías
/// pensado darle otra responsabilidad (arranque de partida, etc.) que
/// no formaba parte de lo que hemos hablado. Si no va a tener más uso,
/// se puede eliminar sin más.
/// </summary>
public class GameMain : MonoBehaviour
{
}