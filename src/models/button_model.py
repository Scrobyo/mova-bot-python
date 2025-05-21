from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
                'layout': [
                    [InlineKeyboardButton(
                        "💵 PIX", callback_data="payment_pix_{plan}")],
                    [InlineKeyboardButton(
                        "💳 CARTÃO", callback_data="payment_cc_{plan}")],
                    [InlineKeyboardButton(
                        "↩️ VOLTAR", callback_data="back_to_plans")]
                ]
            },
            'pix_confirmation': {
                'layout': [
                    [InlineKeyboardButton(
                        "✅ JÁ PAGUEI", callback_data="paid_pix_{plan}")],
                    [InlineKeyboardButton(
                        "↩️ VOLTAR", callback_data="plan_{plan}")]
                ]
            },
            'pix_confirmation_error': {
                'layout': [
                    [InlineKeyboardButton(
                        "✅ JÁ PAGUEI", callback_data="paid_pix_{plan}")],
                    [InlineKeyboardButton(
                        "📞 SUPORTE", url="https://t.me/Scrobyo")]
                ]
            },
            'credit_card_payment': {
                'layout': [
                    [InlineKeyboardButton(
                        "🔒 PAGAR AGORA", url="{payment_url}")],
                    [InlineKeyboardButton(
                        "↩️ VOLTAR", callback_data="plan_{plan}")]
                ]
            },
            'vip_success': {
                'layout': [
                    [InlineKeyboardButton("👉 ACESSAR GRUPO VIP",
                                          url="https://t.me/+Qy9pq5tu-Yw1Njgx")],
                    [InlineKeyboardButton(
                        "🛠 SUPORTE", url="https://t.me/@Scrobyo")]
                ]
            }
        }

    def get(self, key: str, **kwargs) -> InlineKeyboardMarkup:
        if key not in self._buttons:
            return None

        formatted_layout = []
        for row in self._buttons[key]['layout']:
            formatted_row = []
            for button in row:
                callback_or_url = button.callback_data or button.url
                if callback_or_url:
                    formatted_data = callback_or_url.format(**kwargs)

                    if button.url:
                        formatted_row.append(
                            InlineKeyboardButton(
                                text=button.text,
                                url=formatted_data
                            )
                        )
                    else:
                        formatted_row.append(
                            InlineKeyboardButton(
                                text=button.text,
                                callback_data=formatted_data
                            )
                        )
                else:
                    formatted_row.append(button)
            formatted_layout.append(formatted_row)

        return InlineKeyboardMarkup(formatted_layout)
