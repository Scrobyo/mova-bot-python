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

            # Comandos
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
            'help': "🛠 *Comandos disponíveis:*\n\n/start - Iniciar\n/vip - Planos VIP\n/pix - Pagamentos",
            'unknown_command': "⚠️ Comando não reconhecido. Use /ajuda para ver as opções.",

            # VIP
            'vip_plans': "💎 *Planos VIP*:\n\n- 1 Mês: R$20\n- 3 Meses: R$50\n- 1 Ano: R$180",

            # Erros
            'error': "❌ Ocorreu um erro. Por favor, tente novamente."
        }

    def get(self, key: str, **kwargs):
        value = self._messages.get(key, self._messages['error'])

        if isinstance(value, dict):
            # Formata cada submensagem, se houver variáveis
            return {k: v.format(**kwargs) for k, v in value.items()}
        elif isinstance(value, str):
            return value.format(**kwargs)
        return value
