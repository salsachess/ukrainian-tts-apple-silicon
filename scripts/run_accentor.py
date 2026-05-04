#!/usr/bin/env python3
"""
Ukrainian Accentor — Gradio-сервер наголосів.
Працює на CPU — не потребує GPU.
Порт: 7861
"""

import gradio as gr
from ukrainian_accentor_transformer import Accentor

print("[Accentor] Завантаження моделі наголосів...")
accentor = Accentor()
print("[Accentor] Модель готова.")


def accentification(sentence):
    """Розставляє наголоси в українському тексті."""
    accented_sentence = accentor(sentence)
    return accented_sentence


iface = gr.Interface(
    fn=accentification,
    inputs=gr.Textbox(label="Вхідний текст"),
    outputs=gr.Textbox(label="Текст з наголосами"),
    title="Ukrainian Accentor Transformer"
)

if __name__ == "__main__":
    print("[Accentor] Запуск Gradio на порту 7861...")
    iface.launch(server_name="0.0.0.0", server_port=7861)
