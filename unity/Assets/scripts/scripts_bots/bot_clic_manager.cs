using System;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections.Generic;



public class Bot_clic_manager : MonoBehaviour
{

    void Update()
    {
        if (Mouse.current.leftButton.wasPressedThisFrame)
        {
            Vector2 mousePos = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue());
            RaycastHit2D hit = Physics2D.Raycast(mousePos, Vector2.zero);

            if (hit.collider != null)
            {
                // si se hace clic en un bot
                if (hit.collider.TryGetComponent<bot_info>(out var bot_inf))
                {
                    GetComponent<obtener_datos_bot_clic>().clic_en_bot(bot_inf);
                }
            }
        }
    }

}
