from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, List, Tuple


class ButtonModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_buttons()
        return cls._instance

    def _init_buttons(self):
        self._buttons = {
            'vip_plans': {
                'message': "💰 *ESCOLHA SEU PLANO VIP ABAIXO* 💰",
                'layout': [
                    [InlineKeyboardButton(
                        "1️⃣ 1 MÊS - R$19.90", callback_data="plan_1month")],
                    [InlineKeyboardButton(
                        "3️⃣ 3 MESES - R$29.90", callback_data="plan_3months")],
                    [InlineKeyboardButton(
                        "6️⃣ 6 MESES - R$49.90", callback_data="plan_6months")],
                    [InlineKeyboardButton(
                        "❤️ VITALÍCIO - R$79.90", callback_data="plan_lifetime")]
                ]
            },
            'payment_methods': {
                'message': "💳 *SELECIONE A FORMA DE PAGAMENTO*",
                'layout': [
                    [InlineKeyboardButton(
                        "💵 PIX (5% OFF)", callback_data="payment_pix_{plan}")],
                    [InlineKeyboardButton(
                        "💳 CARTÃO DE CRÉDITO", callback_data="payment_cc_{plan}")],
                    [InlineKeyboardButton(
                        "↩️ VOLTAR", callback_data="back_to_plans")]
                ]
            }
        }

    def get(self, key: str, **kwargs) -> Tuple[str, InlineKeyboardMarkup]:
        """Retorna mensagem e teclado formatado"""
        if key not in self._buttons:
            return "", None

        button_data = self._buttons[key]

        # Substitui placeholders nos callback_data
        formatted_layout = []
        for row in button_data['layout']:
            formatted_row = []
            for button in row:
                formatted_callback = button.callback_data.format(**kwargs)
                formatted_row.append(
                    InlineKeyboardButton(
                        text=button.text,
                        callback_data=formatted_callback
                    )
                )
            formatted_layout.append(formatted_row)

        return button_data['message'], InlineKeyboardMarkup(formatted_layout)
