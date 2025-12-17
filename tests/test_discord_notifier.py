import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discord_notifier import DiscordNotifier


class TestDiscordNotifier:
    """Tests pour le module discord_notifier."""
    
    def test_initialization(self):
        """Vérifie l'initialisation du notifier."""
        webhook_url = "https://discord.com/api/webhooks/test"
        bulletin_url = "https://bulletin.test.com"
        
        notifier = DiscordNotifier(webhook_url, bulletin_url)
        
        assert notifier.webhook_url == webhook_url
        assert notifier.bulletin_url == bulletin_url
    
    def test_initialization_without_bulletin_url(self):
        """Vérifie l'initialisation sans URL de bulletin."""
        webhook_url = "https://discord.com/api/webhooks/test"
        
        notifier = DiscordNotifier(webhook_url)
        
        assert notifier.webhook_url == webhook_url
        assert notifier.bulletin_url is None
    
    @patch('discord_notifier.requests.post')
    def test_send_notification_success(self, mock_post):
        """Vérifie l'envoi réussi d'une notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier("https://discord.com/webhook")
        notifier.send_notification("Test Title", "Test Description")
        
        assert mock_post.called
        assert mock_post.call_count == 1
        
        # Vérifier les arguments d'appel
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://discord.com/webhook"
        assert "Content-Type" in call_args[1]["headers"]
    
    @patch('discord_notifier.requests.post')
    def test_send_notification_with_fields(self, mock_post):
        """Vérifie l'envoi d'une notification avec des champs personnalisés."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier("https://discord.com/webhook")
        fields = [
            {"name": "Field1", "value": "Value1", "inline": True},
            {"name": "Field2", "value": "Value2", "inline": False}
        ]
        notifier.send_notification("Test", "Description", fields=fields)
        
        assert mock_post.called
    
    @patch('discord_notifier.requests.post')
    def test_send_notification_failure(self, mock_post):
        """Vérifie la gestion d'erreur lors de l'envoi."""
        mock_post.side_effect = Exception("Network error")
        
        notifier = DiscordNotifier("https://discord.com/webhook")
        # Ne doit pas lever d'exception
        notifier.send_notification("Test", "Description")
        
        assert mock_post.called
    
    def test_send_notification_without_webhook(self, capsys):
        """Vérifie que rien n'est envoyé sans webhook URL."""
        notifier = DiscordNotifier(None)
        notifier.send_notification("Test", "Description")
        
        captured = capsys.readouterr()
        assert "No Discord Webhook URL configured" in captured.out
    
    def test_generate_stats_bar_valid(self):
        """Vérifie la génération du graphique de stats avec des valeurs valides."""
        notifier = DiscordNotifier("https://discord.com/webhook")
        
        result = notifier.generate_stats_bar(8.5, 12.3, 18.0)
        
        assert result is not None
        assert "8.5" in result
        assert "12.3" in result
        assert "18.0" in result
        assert "Min" in result
        assert "Moy" in result
        assert "Max" in result
    
    def test_generate_stats_bar_invalid(self):
        """Vérifie la gestion d'erreur avec des valeurs invalides."""
        notifier = DiscordNotifier("https://discord.com/webhook")
        
        result = notifier.generate_stats_bar("invalid", None, "error")
        
        assert result is None
    
    @patch('discord_notifier.requests.post')
    def test_notify_new_grade(self, mock_post):
        """Vérifie la notification pour une nouvelle note."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier("https://discord.com/webhook", "https://bulletin.url")
        notifier.notify_new_grade(
            module_name="R1.01 - Initiation au développement",
            evaluation_name="TP1",
            note="15.5",
            mean=12.0,
            min_note=5.0,
            max_note=19.0,
            mention_everyone=True
        )
        
        assert mock_post.called
        call_args = mock_post.call_args
        data = call_args[1]['data']
        # Les caractères accentués sont encodés en unicode dans le JSON
        assert "Nouvelle Note Publi" in data or "Publi\\u00e9e" in data
        assert "@everyone" in data
    
    @patch('discord_notifier.requests.post')
    def test_notify_grade_update(self, mock_post):
        """Vérifie la notification pour une modification de note."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = DiscordNotifier("https://discord.com/webhook")
        notifier.notify_grade_update(
            module_name="R1.01 - Initiation au développement",
            evaluation_name="TP1",
            old_note="14.0",
            new_note="15.5"
        )
        
        assert mock_post.called
        call_args = mock_post.call_args
        data = call_args[1]['data']
        # Les caractères accentués sont encodés en unicode dans le JSON
        assert "Note Modifi" in data or "Modifi\\u00e9e" in data
