using System;
using UnityEngine;
using UnityEngine.InputSystem;

public class MoverCamara : MonoBehaviour
{
    private float actualZoom;
    private float velocidad;
    private float zoomSpeed;
    Camera cam;


    public float zoomMin;
    public float zoomMax;



    void Start()
    {
        actualZoom = Camera.main.orthographicSize;

        velocidad = 5f * actualZoom / zoomMin;
        zoomSpeed = 50f * actualZoom / zoomMin;

        zoomMin = 10;
        zoomMax = 100;


        cam = GetComponent<Camera>();
        cam.orthographicSize = zoomMax;
    }

    void Update()
    {
        actualZoom = Camera.main.orthographicSize;
        Vector3 movimiento = new Vector3(0, 0, 0);

        var teclado = Keyboard.current;
        Vector3 dir = Vector3.zero;

        if (teclado.wKey.isPressed) dir += Vector3.up;
        if (teclado.sKey.isPressed) dir += Vector3.down;
        if (teclado.aKey.isPressed) dir += Vector3.left;
        if (teclado.dKey.isPressed) dir += Vector3.right;

        Console.WriteLine("dir: " + dir + ", velocidad: " + velocidad + ", Time.deltaTime: " + Time.deltaTime);
        transform.position += dir * velocidad * Time.deltaTime;

        float scroll = Mouse.current.scroll.ReadValue().y;

        if (scroll != 0)
        {
            cam.orthographicSize -= scroll * zoomSpeed * Time.deltaTime;
            cam.orthographicSize = Mathf.Clamp(cam.orthographicSize, zoomMin, zoomMax);
        }

        zoomSpeed = 50f * actualZoom / zoomMin;
        velocidad = 5f * actualZoom / zoomMin;

    }
}
