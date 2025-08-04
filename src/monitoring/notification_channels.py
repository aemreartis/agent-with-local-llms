"""
Notification Channel Definitions

Defines various notification channels for alert delivery.
"""

from typing import Dict, List, Any


class NotificationChannels:
    """Notification channel definitions for Grafana"""
    
    def get_email_channel(self) -> Dict[str, Any]:
        """Get email notification channel configuration"""
        return {
            'name': 'Email Notifications',
            'type': 'email',
            'settings': {
                'addresses': 'admin@example.com,ops@example.com',
                'singleEmail': True
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '1h'
        }
    
    def get_slack_channel(self) -> Dict[str, Any]:
        """Get Slack notification channel configuration"""
        return {
            'name': 'Slack Notifications',
            'type': 'slack',
            'settings': {
                'url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
                'channel': '#alerts',
                'username': 'Grafana Alerts',
                'iconEmoji': ':warning:',
                'iconUrl': '',
                'title': '{{ .CommonAnnotations.summary }}',
                'text': '{{ .CommonAnnotations.description }}'
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '1h'
        }
    
    def get_webhook_channel(self) -> Dict[str, Any]:
        """Get webhook notification channel configuration"""
        return {
            'name': 'Webhook Notifications',
            'type': 'webhook',
            'settings': {
                'url': 'https://your-webhook-endpoint.com/alerts',
                'httpMethod': 'POST',
                'maxAlerts': 0,
                'title': '{{ .CommonAnnotations.summary }}',
                'message': '{{ .CommonAnnotations.description }}',
                'username': '',
                'password': ''
            },
            'isDefault': False,
            'sendReminder': False,
            'frequency': '1h'
        }
    
    def get_pagerduty_channel(self) -> Dict[str, Any]:
        """Get PagerDuty notification channel configuration"""
        return {
            'name': 'PagerDuty Notifications',
            'type': 'pagerduty',
            'settings': {
                'integrationKey': 'YOUR_PAGERDUTY_INTEGRATION_KEY',
                'severity': '{{ if eq .CommonLabels.severity "critical" }}critical{{ else }}warning{{ end }}',
                'class': 'Grafana Alert',
                'group': 'Agentic RAG System',
                'summary': '{{ .CommonAnnotations.summary }}',
                'description': '{{ .CommonAnnotations.description }}'
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '30m'
        }
    
    def get_teams_channel(self) -> Dict[str, Any]:
        """Get Microsoft Teams notification channel configuration"""
        return {
            'name': 'Teams Notifications',
            'type': 'teams',
            'settings': {
                'url': 'https://your-org.webhook.office.com/webhookb2/YOUR/TEAMS/WEBHOOK',
                'title': '{{ .CommonAnnotations.summary }}',
                'message': '{{ .CommonAnnotations.description }}',
                'sectionTitle': 'Alert Details'
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '1h'
        }
    
    def get_discord_channel(self) -> Dict[str, Any]:
        """Get Discord notification channel configuration"""
        return {
            'name': 'Discord Notifications',
            'type': 'discord',
            'settings': {
                'url': 'https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK',
                'title': '{{ .CommonAnnotations.summary }}',
                'message': '{{ .CommonAnnotations.description }}',
                'use_discord_username': False
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '1h'
        }
    
    def get_telegram_channel(self) -> Dict[str, Any]:
        """Get Telegram notification channel configuration"""
        return {
            'name': 'Telegram Notifications',
            'type': 'telegram',
            'settings': {
                'bottoken': 'YOUR_TELEGRAM_BOT_TOKEN',
                'chatid': 'YOUR_CHAT_ID',
                'message': '{{ .CommonAnnotations.summary }}\n\n{{ .CommonAnnotations.description }}',
                'parseMode': 'HTML'
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '1h'
        }
    
    def get_opsgenie_channel(self) -> Dict[str, Any]:
        """Get OpsGenie notification channel configuration"""
        return {
            'name': 'OpsGenie Notifications',
            'type': 'opsgenie',
            'settings': {
                'apiKey': 'YOUR_OPSGENIE_API_KEY',
                'apiUrl': 'https://api.opsgenie.com/',
                'message': '{{ .CommonAnnotations.summary }}',
                'description': '{{ .CommonAnnotations.description }}',
                'autoClose': True,
                'overridePriority': True,
                'sendTagsAs': 'both'
            },
            'isDefault': False,
            'sendReminder': True,
            'frequency': '30m'
        }
    
    def get_all_channels(self) -> Dict[str, Dict[str, Any]]:
        """Get all notification channels"""
        return {
            'email': self.get_email_channel(),
            'slack': self.get_slack_channel(),
            'webhook': self.get_webhook_channel(),
            'pagerduty': self.get_pagerduty_channel(),
            'teams': self.get_teams_channel(),
            'discord': self.get_discord_channel(),
            'telegram': self.get_telegram_channel(),
            'opsgenie': self.get_opsgenie_channel()
        } 