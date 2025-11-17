using System;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections.Generic;



public class BotClicManager : MonoBehaviour
{

    IBotsLogica botsLogica;

    private void Start()
    {
        botsLogica = ServiceLocator.Instance.Get<IBotsLogica>();
    }

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
                    botsLogica.ClicEnBot(bot_inf);
                }
            }
        }
    }

}
