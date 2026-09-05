using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Camera))]
public class MoverCamaraWASD : MonoBehaviour
{
    float actualZoom;
    float velocidad;
    float zoomSpeed;

    public Camera cam;
    public float zoomMin;
    public float zoomMax;
    public float factorVelocidad;
    public float factorZoom;

    // ---- Esquinas de la cámara, solo para inspección en el Inspector ----
    // Se recalculan cada frame en Update() (ver ActualizarEsquinas), así
    // que cualquier valor que edites aquí a mano en el Inspector se
    // sobreescribe de inmediato -- son de solo lectura en la práctica,
    // no hace falta un atributo ReadOnly a medida para algo tan simple.
    [Header("Esquinas de cámara (solo lectura, depuración)")]
    [SerializeField] private Vector3 esquinaInferiorIzquierda;
    [SerializeField] private Vector3 esquinaInferiorDerecha;
    [SerializeField] private Vector3 esquinaSuperiorIzquierda;
    [SerializeField] private Vector3 esquinaSuperiorDerecha;

    void Awake()
    {
        actualZoom = Camera.main.orthographicSize;
        velocidad = factorVelocidad * actualZoom / zoomMin;
        zoomSpeed = factorZoom * actualZoom / zoomMin;
        cam.orthographicSize = zoomMax;
    }

    void Update()
    {
        actualZoom = Camera.main.orthographicSize;

        var teclado = Keyboard.current;
        Vector3 dir = Vector3.zero;

        if (teclado.wKey.isPressed) dir += Vector3.up;
        if (teclado.sKey.isPressed) dir += Vector3.down;
        if (teclado.aKey.isPressed) dir += Vector3.left;
        if (teclado.dKey.isPressed) dir += Vector3.right;

        if (dir.x != 0 ||
            dir.y != 0)
        {
            // TODO: llamar a la funcion que corta que la camara persiga a un elemento
        }
        transform.position += Time.deltaTime * velocidad * dir;

        float scroll = Mouse.current.scroll.ReadValue().y;

        if (scroll != 0)
        {
            cam.orthographicSize -= scroll * zoomSpeed * Time.deltaTime;
            cam.orthographicSize = Mathf.Clamp(cam.orthographicSize, zoomMin, zoomMax);
        }

        zoomSpeed = factorZoom * actualZoom / zoomMin;
        velocidad = factorVelocidad * actualZoom / zoomMin;

        ActualizarEsquinas();
    }

    /// <summary>
    /// Calcula las 4 esquinas del encuadre visible en coordenadas de
    /// mundo, a partir de orthographicSize/aspect -- mismo cálculo que
    /// FocoMasterController.CalcularRegionVisible(), pero aquí es solo
    /// para verlo en el Inspector mientras juegas/paneas/zoomeas, no
    /// para mandar nada al servidor.
    /// </summary>
    private void ActualizarEsquinas()
    {
        float alto = cam.orthographicSize * 2f;
        float ancho = alto * cam.aspect;
        Vector3 centro = cam.transform.position;

        float minX = centro.x - ancho / 2f;
        float maxX = centro.x + ancho / 2f;
        float minY = centro.y - alto / 2f;
        float maxY = centro.y + alto / 2f;

        esquinaInferiorIzquierda = new Vector3(minX, minY, centro.z);
        esquinaInferiorDerecha = new Vector3(maxX, minY, centro.z);
        esquinaSuperiorIzquierda = new Vector3(minX, maxY, centro.z);
        esquinaSuperiorDerecha = new Vector3(maxX, maxY, centro.z);
    }
}