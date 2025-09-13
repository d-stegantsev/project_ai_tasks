from odoo import http
from odoo.http import request

class AiChatController(http.Controller):

    @http.route("/ai_chat/create_task", type="http", auth="user")
    def create_task(self, **kwargs):
        return request.redirect("/web#action=project_ai_tasks.open_ai_task_wizard")

    @http.route("/ai_chat/change_task", type="http", auth="user")
    def change_task(self, task_id=None, **kwargs):
        ctx = {}
        if task_id:
            task = request.env["project.task"].browse(int(task_id))
            if task.exists():
                ctx = {
                    "default_mode": "change",
                    "default_task_id": task.id,
                    "default_project_id": task.project_id.id,
                    "default_name": task.name,
                    "default_description": task.description,
                    "default_user_id": task.user_ids[:1].id,
                    "default_date_deadline": task.date_deadline,
                    "default_priority": task.priority,
                }
        return request.redirect(
            "/web#action=project_ai_tasks.open_ai_change_task_wizard&active_id=%s&context=%s"
            % (task_id or "", ctx)
        )
