from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class ProjectTask(models.Model):
    _inherit = "project.task"

    ai_feedback = fields.Text(
        string="AI Feedback",
        help="AI-generated notes or review for this task."
    )

    ai_status = fields.Selection(
        [
            ("paused", "Paused"),
            ("cancelled", "Cancelled"),
            ("needs_review", "Needs Review"),
        ],
        string="AI Status",
        help="Lightweight workflow flag controlled by chat-commands or checks."
    )

    ai_tags = fields.Many2many(
        comodel_name="project.tags",
        relation="project_task_ai_tags_rel",
        column1="task_id",
        column2="tag_id",
        string="AI Tags",
        help="Tags suggested by AI based on the task description."
    )

    # --- validations ---
    @api.constrains("name")
    def _check_title_words(self):
        for rec in self:
            if rec.name and len(rec.name.split()) < 5:
                raise ValidationError(_("Title must contain at least 5 words."))

    @api.constrains("date_deadline")
    def _check_deadline(self):
        for rec in self:
            if rec.date_deadline:
                tomorrow = date.today() + timedelta(days=1)
                in_one_year = date.today() + timedelta(days=365)
                if rec.date_deadline < tomorrow or rec.date_deadline > in_one_year:
                    raise ValidationError(_("Deadline must be from tomorrow and within one year."))

    # Block project change for non-PM
    def write(self, vals):
        if "project_id" in vals and not self.env.user.has_group("project_ai_tasks.group_ai_pm"):
            raise AccessError(_("Only PM can change the project of a task."))
        return super().write(vals)

    # --- actions (buttons) ---
    def _post_note(self, body):
        for rec in self:
            rec.message_post(body=body)

    def action_pause(self):
        self.write({"ai_status": "paused"})
        self._post_note(_("Task was paused."))

    def action_resume(self):
        self.write({"ai_status": False})
        self._post_note(_("Task was resumed."))

    def action_cancel(self):
        self.write({"ai_status": "cancelled"})
        self._post_note(_("Task was cancelled."))

    def action_return(self):
        self.write({"ai_status": "needs_review"})
        self._post_note(_("#needs_review: Task was returned to PM."))

    def action_approve(self):
        self.write({"ai_status": False})
        self._post_note(_("Task approved by PM."))

    def action_complete(self):
        # Mark as done at Kanban level and notify
        self.write({"kanban_state": "done"})
        self._post_note(_("Task was completed by assignee."))
