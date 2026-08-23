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
            dir.y != 0 ||
            dir.z != 0)
        {
            Debug.Log("DejarDeSeguirConCamara()");
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
    }
}
