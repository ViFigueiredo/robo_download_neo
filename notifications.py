"""
Módulo para gerenciar notificações em diferentes serviços externos.
Suporta: Slack, Telegram, Email, Webhook genérico
"""

import logging
import os
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationManager:
    """Gerencia notificações em múltiplos serviços."""
    
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
        self.slack_channel = os.getenv("SLACK_CHANNEL", "#robo-downloads").strip()
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        
        self.email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.email_smtp = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com").strip()
        self.email_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM", "").strip()
        self.email_password = os.getenv("EMAIL_PASSWORD", "").strip()
        self.email_to = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
        
        self.webhook_url = os.getenv("WEBHOOK_URL", "").strip()
        self.webhook_token = os.getenv("WEBHOOK_TOKEN", "").strip()
        
        # Validação básica
        self._validar_configuracao()
    
    def _validar_configuracao(self):
        """Valida a configuração dos serviços de notificação."""
        if not any([self.slack_webhook, self.telegram_token, self.email_enabled, self.webhook_url]):
            logger.info("Nenhum serviço de notificação configurado")
        else:
            if self.slack_webhook:
                logger.info(f"✓ Slack notificações ativadas (canal: {self.slack_channel})")
            if self.telegram_token:
                logger.info(f"✓ Telegram notificações ativadas (chat: {self.telegram_chat_id})")
            if self.email_enabled and self.email_to:
                logger.info(f"✓ Email notificações ativadas para: {', '.join(self.email_to)}")
            if self.webhook_url:
                logger.info(f"✓ Webhook notificações ativadas")
    
    def notificar_sucesso(self, resumo: Dict[str, Any]):
        """Envia notificação de sucesso."""
        titulo = "✅ Robô de Download - SUCESSO"
        corpo = self._formatar_resumo(resumo, "sucesso")
        self._enviar_notificacoes(titulo, corpo, "success")
    
    def notificar_erro(self, erro: str, resumo: Optional[Dict[str, Any]] = None):
        """Envia notificação de erro."""
        titulo = "❌ Robô de Download - ERRO"
        if resumo:
            corpo = f"**Erro:** {erro}\n\n{self._formatar_resumo(resumo, 'erro')}"
        else:
            corpo = f"**Erro:** {erro}"
        self._enviar_notificacoes(titulo, corpo, "error")
    
    def notificar_aviso(self, mensagem: str):
        """Envia notificação de aviso."""
        titulo = "⚠️ Robô de Download - AVISO"
        self._enviar_notificacoes(titulo, mensagem, "warning")
    
    def _formatar_resumo(self, resumo: Dict[str, Any], tipo: str) -> str:
        """Formata o resumo da execução para notificação."""
        linhas = []
        
        if resumo.get("inicio"):
            linhas.append(f"📅 Iniciado: {resumo['inicio']}")
        
        if resumo.get("atividades_status"):
            linhas.append(f"📊 Atividades/Status: {resumo['atividades_status']}")
        
        if resumo.get("atividades"):
            linhas.append(f"📋 Atividades: {resumo['atividades']}")
        
        if resumo.get("producao"):
            linhas.append(f"📈 Produção: {resumo['producao']}")
        
        if resumo.get("arquivos"):
            linhas.append(f"✓ Arquivos baixados: {len(resumo['arquivos'])}")
            for arquivo in resumo["arquivos"][:5]:  # Mostra até 5
                linhas.append(f"  • {arquivo}")
            if len(resumo["arquivos"]) > 5:
                linhas.append(f"  ... e mais {len(resumo['arquivos']) - 5}")
        
        if resumo.get("metricas"):
            metricas = resumo["metricas"]
            linhas.append(f"⏱️ Tempo total: {metricas.get('tempo_total', 0):.2f}s")
            linhas.append(f"⏱️ Tempo de download: {metricas.get('tempo_download', 0):.2f}s")
        
        if resumo.get("fim"):
            linhas.append(f"✓ Finalizado: {resumo['fim']}")
        
        return "\n".join(linhas)
    
    def _enviar_notificacoes(self, titulo: str, corpo: str, tipo: str):
        """Envia notificação para todos os serviços configurados."""
        if self.slack_webhook:
            self._enviar_slack(titulo, corpo, tipo)
        
        if self.telegram_token:
            self._enviar_telegram(titulo, corpo)
        
        if self.email_enabled and self.email_to:
            self._enviar_email(titulo, corpo)
        
        if self.webhook_url:
            self._enviar_webhook(titulo, corpo, tipo)
    
    def _enviar_slack(self, titulo: str, corpo: str, tipo: str):
        """Envia mensagem para Slack via webhook."""
        try:
            cor_mapa = {
                "success": "#36a64f",
                "error": "#ff0000",
                "warning": "#ffaa00"
            }
            
            payload = {
                "channel": self.slack_channel,
                "attachments": [{
                    "fallback": titulo,
                    "title": titulo,
                    "text": corpo,
                    "color": cor_mapa.get(tipo, "#808080"),
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("✓ Notificação Slack enviada com sucesso")
            else:
                logger.warning(f"Erro ao enviar Slack: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação Slack: {e}")
    
    def _enviar_telegram(self, titulo: str, corpo: str):
        """Envia mensagem para Telegram."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            mensagem = f"*{titulo}*\n\n{corpo}"
            
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": mensagem,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("✓ Notificação Telegram enviada com sucesso")
            else:
                logger.warning(f"Erro ao enviar Telegram: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação Telegram: {e}")
    
    def _enviar_email(self, titulo: str, corpo: str):
        """Envia email de notificação."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            msg['Subject'] = titulo
            
            # Converter para HTML simples
            corpo_html = corpo.replace('\n', '<br>')
            msg.attach(MIMEText(corpo_html, 'html'))
            
            with smtplib.SMTP(self.email_smtp, self.email_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            logger.info(f"✓ Email enviado para {', '.join(self.email_to)}")
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    def _enviar_webhook(self, titulo: str, corpo: str, tipo: str):
        """Envia dados para webhook genérico."""
        try:
            payload = {
                "title": titulo,
                "body": corpo,
                "type": tipo,
                "timestamp": datetime.now().isoformat()
            }
            
            headers = {"Content-Type": "application/json"}
            if self.webhook_token:
                headers["Authorization"] = f"Bearer {self.webhook_token}"
            
            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                logger.info("✓ Notificação webhook enviada com sucesso")
            else:
                logger.warning(f"Erro ao enviar webhook: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação webhook: {e}")


class MetricsCollector:
    """Coleta métricas de execução."""
    
    def __init__(self):
        self.enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.metricas = {}
        self.tempos_etapas = {}
        self.inicio_geral = None
        
        if self.enabled:
            logger.info("✓ Coleta de métricas ativada")
    
    def iniciar(self):
        """Marca o início da execução."""
        if not self.enabled:
            return
        
        self.inicio_geral = datetime.now()
        self.tempos_etapas = {}
        logger.debug("Métricas: Execução iniciada")
    
    def marcar_etapa(self, nome_etapa: str, tempo_segundos: Optional[float] = None):
        """Marca o tempo de uma etapa."""
        if not self.enabled:
            return
        
        if tempo_segundos is None:
            self.tempos_etapas[nome_etapa] = datetime.now()
        else:
            self.tempos_etapas[nome_etapa] = tempo_segundos
            logger.debug(f"Métrica: {nome_etapa} = {tempo_segundos:.2f}s")
    
    def finalizar(self) -> Dict[str, Any]:
        """Finaliza a coleta e retorna as métricas."""
        if not self.enabled or not self.inicio_geral:
            return {}
        
        tempo_total = (datetime.now() - self.inicio_geral).total_seconds()
        
        self.metricas = {
            "tempo_total": tempo_total,
            "etapas": {}
        }
        
        for etapa, valor in self.tempos_etapas.items():
            if isinstance(valor, float) or isinstance(valor, int):
                self.metricas["etapas"][etapa] = valor
            else:
                # Se for datetime, calcular diferença
                self.metricas["etapas"][etapa] = (datetime.now() - valor).total_seconds()
        
        logger.info(f"Tempo total de execução: {tempo_total:.2f}s")
        for etapa, tempo in self.metricas["etapas"].items():
            logger.info(f"  {etapa}: {tempo:.2f}s")
        
        return self.metricas
    
    def obter_metricas(self) -> Dict[str, Any]:
        """Retorna as métricas coletadas."""
        return self.metricas


# Instâncias globais
notification_manager = NotificationManager()
metrics_collector = MetricsCollector()
