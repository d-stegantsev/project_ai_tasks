from odoo import models, _


class ProjectAiCommandService(models.AbstractModel):
    _name = "project.ai.command.service"
    _description = "AI Command Service for Project Tasks"

    # ----------------------------------------------------
    # Map: command → (handler, allowed_groups, description)
    # ----------------------------------------------------
    _commands_map = {
        "/list_tasks": ("_cmd_list_tasks", ["base.group_user"], "Show your tasks"),
        "/create_task": ("_cmd_create_task", ["base.group_user"], "Create new task"),
        "/change_task": ("_cmd_change_task", ["project_ai_tasks.group_ai_pm"], "Update task fields"),
        "/edit_task": ("_cmd_edit_task", ["project_ai_tasks.group_ai_pm", "project_ai_tasks.group_ai_dev"], "Edit returned task"),
        "/pause_task": ("_cmd_pause_task", ["project_ai_tasks.group_ai_pm", "project_ai_tasks.group_ai_dev"], "Pause task"),
        "/resume_task": ("_cmd_resume_task", ["project_ai_tasks.group_ai_pm", "project_ai_tasks.group_ai_dev"], "Resume paused task"),
        "/cancel_task": ("_cmd_cancel_task", ["project_ai_tasks.group_ai_pm", "project_ai_tasks.group_ai_dev"], "Cancel task"),
        "/complete_task": ("_cmd_complete_task", ["project_ai_tasks.group_ai_dev"], "Mark task as completed"),
        "/return_task": ("_cmd_return_task", ["project_ai_tasks.group_ai_pm"], "Return task to PM"),
        "/approve_task": ("_cmd_approve_task", ["project_ai_tasks.group_ai_pm"], "Approve task"),
        "/assign_task": ("_cmd_assign_task", ["project_ai_tasks.group_ai_pm"], "Reassign task to another user"),
        "/comment_task": ("_cmd_comment_task", ["project_ai_tasks.group_ai_pm", "project_ai_tasks.group_ai_dev"], "Add a comment to task"),
        "/ai_help": ("_cmd_ai_help", ["base.group_user"], "Show available commands"),
    }

    # -----------------------------
    # Dispatcher
    # -----------------------------
    def build_reply(self, command, args, author):
        """Route command to correct handler if user has rights"""
        cmd_info = self._commands_map.get(command)
        if not cmd_info:
            return _("Unknown command: %s") % command

        method_name, groups, _desc = cmd_info

        # Superuser (Admin) always has access
        if author.id != self.env.ref("base.user_admin").id:
            if not any(author.has_group(g) for g in groups):
                return _("You don't have access to this command.")

        handler = getattr(self, method_name, None)
        if not handler:
            return _("Command not implemented: %s") % command

        return handler(args, author)

    def parse_and_reply(self, body, author):
        """Handle incoming body with optional command prefix '/'.
        Returns reply string or None if not a command.
        """
        if not body or not body.startswith("/"):
            return None
        parts = body.split()
        command, args = parts[0], parts[1:]
        return self.build_reply(command, args, author)

    # -----------------------------
    # Command Implementations
    # -----------------------------
    def _cmd_ai_help(self, args, author):
        """Show only commands allowed for the user"""
        available = []
        for cmd, (method, groups, desc) in self._commands_map.items():
            if author.id == self.env.ref("base.user_admin").id or any(author.has_group(g) for g in groups):
                available.append(f"{cmd} — {desc}")
        return "*Available AI Commands*:<br/>" + "<br/>".join(available)

    def _cmd_list_tasks(self, args, author):
        tasks = self.env["project.task"].search([("user_ids", "in", author.id)], limit=5)
        if not tasks:
            return _("No tasks found.")
        return "<br/>".join([_(f"[{t.id}] {t.name} ({t.stage_id.name})") for t in tasks])

    def _cmd_create_task(self, args, author):
        """
        Send link to open wizard for creating a new task.
        """
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        link = f"{base_url}/ai_chat/create_task"
        return f"📌 <b>Create Task Wizard</b>: <a href='{link}'>Open Wizard</a>"

    def _cmd_change_task(self, args, author):
        """Handle /change_task <id> command.
        Returns a clickable link to open the wizard in edit mode.
        """
        if not args:
            return _("Usage: /change_task <id>")

        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")

        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id

        # Return link instead of action-dict
        return _(
            '<a href="/ai_chat/change_task?task_id=%s" target="_blank">'
            'Click here to edit Task %s via wizard</a>'
        ) % (task.id, task.id)

    def _cmd_edit_task(self, args, author):
        """Open wizard for editing an existing task after feedback (via link)."""
        if not args:
            return _("Usage: /edit_task <id>")
        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")

        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id

        return _(
            '<a href="/ai_chat/change_task?task_id=%s" target="_blank">'
            'Edit Task %s via wizard</a>'
        ) % (task.id, task.id)

    def _cmd_pause_task(self, args, author):
        return self._update_status(args, "paused", _("Task paused."))

    def _cmd_resume_task(self, args, author):
        return self._update_status(args, False, _("Task resumed."))

    def _cmd_cancel_task(self, args, author):
        return self._update_status(args, "cancelled", _("Task cancelled."))

    def _cmd_complete_task(self, args, author):
        if not args:
            return _("Usage: /complete_task <id>")
        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")
        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id
        task.write({"kanban_state": "done"})
        task.message_post(body=_("Task marked as completed."))
        return _("Task [%s] marked as done.") % task.id

    def _cmd_return_task(self, args, author):
        return self._update_status(args, "needs_review", _("Task sent back to PM for review."))

    def _cmd_approve_task(self, args, author):
        return self._update_status(args, False, _("Task approved by PM."))

    def _cmd_assign_task(self, args, author):
        if len(args) < 2:
            return _("Usage: /assign_task <id> @username")
        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")
        username = args[1].lstrip("@")
        user = self.env["res.users"].search([("login", "=", username)], limit=1)
        if not user:
            return _("User not found: %s") % username
        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id
        task.write({"user_ids": [(6, 0, [user.id])]})
        task.message_post(body=_("Task reassigned to %s.") % user.name)
        return _("Task [%s] reassigned to %s.") % (task.id, user.name)

    def _cmd_comment_task(self, args, author):
        if len(args) < 2:
            return _("Usage: /comment_task <id> <text>")
        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")
        comment = " ".join(args[1:])
        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id
        task.message_post(body=comment)
        return _("Comment added to Task [%s].") % task.id

    # -----------------------------
    # Helpers
    # -----------------------------
    def _update_status(self, args, status_value, message):
        if not args:
            return _("Usage: /command <id>")
        try:
            task_id = int(args[0])
        except ValueError:
            return _("Invalid task ID.")
        task = self.env["project.task"].browse(task_id)
        if not task.exists():
            return _("Task not found: %s") % task_id
        task.write({"ai_status": status_value})
        task.message_post(body=message)
        return _("Task [%s]: %s") % (task.id, message)
