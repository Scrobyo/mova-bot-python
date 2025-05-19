class MessageModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_messages()
        return cls._instance

    def _init_messages(self):
        self._messages = {
            # Mensagens genéricas
            'generic_response': "Olá {name}! Digite /start para iniciar 🔥",

            # Fluxo de boas-vindas
            'start': {
                'welcome': "🔥 *BEM-VINDO AO LUXURIANET, {name}!* 🔥\n\n",
                'teaser': "🎬 *A gostosinha da Emily Ferrer é uma das muitas que você encontra aqui...*\n\n",
                'cta': "💎 *O GRUPO MAIS COMPLETO E ATUALIZADO DO TELEGRAM!* 💎\n\n"
                       "✅ Mais de *400 gostosas* do OnlyFans, Privacy, etc.\n"
                       "✅ Suporte *24h por dia*\n"
                       "✅ Atualizações *diárias com novidades*\n"
                       "✅ Mídias *100% organizadas* pra facilitar seu acesso\n\n"
                       "🚀 *Assine o VIP agora e desbloqueie tudo sem limites!*"
            },

            # Planos VIP
            'vip_plans': "💎 *ESCOLHA SEU PLANO VIP ABAIXO* 💎",

            'selected_plan': "🎯 *PLANO SELECIONADO:* {plan_name}\n\n"
            "💰 *SELECIONE A FORMA DE PAGAMENTO*",

            # Pagamentos
            'pix_payment': "🔹 *PAGAMENTO VIA PIX* 🔹\n\n"
            "💰 *Valor:* R$ {amount:.2f}\n"
            "⏳ *Expira em:* 24 horas\n\n"
            "📲 *Código PIX (copie e cole no seu banco):*\n"
            "`{qr_code}`\n\n",

            'payment_success': {
                'title': "🎉 *PAGAMENTO CONFIRMADO!* 🎉\n\n",
                'message': "Seu pagamento foi aprovado e seu acesso VIP foi ativado!\n\n"
                "📅 *Validade:* {expiration_date}\n"
                "💰 *Plano:* {plan_name}\n\n"
                "Agora você tem acesso completo ao grupo VIP!",
                'instructions': "👉 Clique no botão abaixo para acessar o grupo VIP:"
            },

            'credit_card_payment': "🚀 *PAGAMENTO POR CARTÃO* 🚀\n\n"
            "Clique no botão abaixo para pagar com segurança:",

            'payment_success': {
                'title': "🎉 *PAGAMENTO CONFIRMADO!* 🎉\n\n",
                'message': "Seu pagamento foi aprovado e seu acesso VIP foi ativado!\n\n"
                "📅 *Validade:* {expiration_date}\n"
                "💰 *Plano:* {plan_name}\n\n"
                "Agora você tem acesso completo ao grupo VIP!",
                'instructions': "👉 Clique no botão abaixo para acessar o grupo VIP:"
            },

            'payment_pending': "🕒 *PAGAMENTO EM PROCESSAMENTO*\n\n"
            "Estamos verificando seu pagamento. Você receberá uma "
            "mensagem assim que for confirmado.\n\n"
            "⏳ Por favor, aguarde...",

            'payment_failed': "❌ *PAGAMENTO NÃO CONFIRMADO*\n\n"
            "Não foi possível confirmar seu pagamento. Por favor, tente novamente.\n\n"
            "Se o problema persistir, entre em contato com o suporte.",

            # Erros
            'pix_error': "❌ Erro ao processar PIX: {error}",
            'cc_error': "❌ Erro ao gerar link de pagamento: {error}",
            'unknown_command': "⚠️ Comando não reconhecido. Use /ajuda para ver as opções."
        }

    def get(self, key: str, **kwargs):
        value = self._messages.get(key, "❌ Mensagem não encontrada")

        if isinstance(value, dict):
            return {k: v.format(**kwargs) for k, v in value.items()}
        elif isinstance(value, str):
            return value.format(**kwargs)
        return value
