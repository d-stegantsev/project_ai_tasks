from odoo import models
from odoo.tools import html2plaintext


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_post(self, **kwargs):
        body = kwargs.get("body", "")
        author = self.env.user
        # normalize HTML -> text
        body_text = html2plaintext(body) if body else ""
        reply = self.env["project.ai.command.service"].parse_and_reply(body_text, author)
        if reply:
            if isinstance(reply, dict) and reply.get("type") == "ir.actions.act_window":
                return reply
            kwargs["body"] = reply
        return super().message_post(**kwargs)
