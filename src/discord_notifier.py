import requests
import json
from datetime import datetime

class DiscordNotifier:
    def __init__(self, webhook_url, bulletin_url=None):
        self.webhook_url = webhook_url
        self.bulletin_url = bulletin_url

    def send_notification(self, title, description, fields=None, color=0x0099cc, content=None):
        if not self.webhook_url:
            print("No Discord Webhook URL configured. Skipping notification.")
            return

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "ScodocAlert"
            }
        }

        if fields:
            embed["fields"] = fields

        payload = {
            "embeds": [embed]
        }
        
        if content:
            payload["content"] = content

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            print(f"Notification sent: {title}")
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")

    def generate_stats_bar(self, min_note, avg_note, max_note):
        """
        Generates a text-based visual representation of the grade distribution (Min/Avg/Max).
        Example: 0..[Min]--(Avg)--[Max]..20
        """
        try:
            mn = float(min_note)
            av = float(avg_note)
            mx = float(max_note)
        except (ValueError, TypeError):
            return None

        # Simple representation
        return f"📉 Min: **{mn}** | 📊 Moy: **{av}** | 📈 Max: **{mx}**"

    def notify_new_grade(self, module_name, evaluation_name, note, mean=None, min_note=None, max_note=None, mention_everyone=False):
        """
        Helper to format a new grade notification.
        """
        fields = [
            {"name": "Module", "value": module_name, "inline": True},
            {"name": "Évaluation", "value": evaluation_name, "inline": True},
            # {"name": "Note", "value": f"**{note}**", "inline": False} # Hidden for privacy
        ]

        stats_bar = self.generate_stats_bar(min_note, mean, max_note)
        if stats_bar:
             fields.append({"name": "Statistiques Promo", "value": stats_bar, "inline": False})

        if self.bulletin_url:
            fields.append({"name": "Lien", "value": f"[Consulter le bulletin]({self.bulletin_url})", "inline": False})

        self.send_notification(
            title="Nouvelle Note Publiée !",
            description=f"Une nouvelle note est disponible en **{module_name}**.",
            fields=fields,
            color=0x43b581,
            content="@everyone" if mention_everyone else None
        )

    def notify_grade_update(self, module_name, evaluation_name, old_note, new_note):
        """
        Helper to format a grade update notification.
        """
        fields = [
            # {"name": "Ancienne Note", "value": str(old_note), "inline": True}, # Hidden for privacy
            # {"name": "Nouvelle Note", "value": f"**{new_note}**", "inline": True} # Hidden for privacy
            {"name": "Info", "value": "Consultez votre relevé pour voir la modification.", "inline": False}
        ]

        if self.bulletin_url:
            fields.append({"name": "Lien", "value": f"[Consulter le bulletin]({self.bulletin_url})", "inline": False})

        self.send_notification(
            title="Note Modifiée",
            description=f"La note de **{evaluation_name}** ({module_name}) a été modifiée.",
            fields=fields,
            color=0xffa500
        )
