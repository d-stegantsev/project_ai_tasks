from datetime import date, timedelta
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AiTaskWizard(models.TransientModel):
    """
    Transient wizard to create or change a task with basic rules + simple AI tag suggestions.
    """
    _name = "project.ai.task.wizard"
    _description = "AI Task Wizard"

    # Mode: create new task or change existing one
    mode = fields.Selection(
        [("create", "Create Task"), ("change", "Change Task")],
        default="create",
        required=True,
        string="Mode",
    )

    project_id = fields.Many2one("project.project", string="Project", required=True)
    task_id = fields.Many2one("project.task", string="Task to Change")

    name = fields.Char(string="Title", help="Short, descriptive title.", required=True)
    description = fields.Text(string="Description")
    user_id = fields.Many2one("res.users", string="Assignee", required=True)
    date_deadline = fields.Date(string="Deadline")
    priority = fields.Selection(
        [("0", "Low"), ("1", "High")], string="Priority", default="0"
    )
    tag_names = fields.Char(
        string="Tags (comma separated)",
        help="Optional. Example: bug, api, urgent",
    )
    spec_url = fields.Char(
        string="Specification URL",
        help="Provide spec link if description mentions API/spec.",
    )

    # --- helpers ---
    def _suggest_tags(self, text: str) -> list[str]:
        """
        Suggest tags for a task based on its description.

        Current implementation: simple keyword-based matcher.
        Later this can be replaced by an LLM integration
        (e.g., OpenAI API call to generate semantic tags).
        """
        text = (text or "").lower()
        tags = set()

        if any(w in text for w in ["bug", "fix", "error", "traceback"]):
            tags.add("bug")
        if any(w in text for w in ["api", "endpoint", "swagger", "openapi"]):
            tags.add("api")
        if any(w in text for w in ["urgent", "asap", "p0", "p1"]):
            tags.add("urgent")
        if any(w in text for w in ["feature", "new", "implement"]):
            tags.add("feature")

        return sorted(tags)

    def _tag_records(self, project_task, names: list[str]):
        """Create/get project.tags by names and link them to the task."""
        Tag = self.env["project.tags"]
        if not names:
            return
        tag_ids = []
        for raw in names:
            name = raw.strip()
            if not name:
                continue
            tag = Tag.search([("name", "=ilike", name)], limit=1)
            if not tag:
                tag = Tag.create({"name": name})
            tag_ids.append(tag.id)
        if tag_ids:
            project_task.write({"ai_tags": [(6, 0, tag_ids)]})

    # --- validations ---
    def _validate(self):
        # Title: at least 5 words
        if not self.name or len(self.name.split()) < 5:
            raise ValidationError(_("Title must contain at least 5 words."))

        # Deadline: from tomorrow and within one year
        if self.date_deadline:
            tomorrow = date.today() + timedelta(days=1)
            in_one_year = date.today() + timedelta(days=365)
            if self.date_deadline < tomorrow or self.date_deadline > in_one_year:
                raise ValidationError(_("Deadline must be from tomorrow and within one year."))

        # Assignee must be set
        if not self.user_id:
            raise ValidationError(_("Assignee is required."))

        # If description mentions API/spec -> spec_url is required
        desc = (self.description or "").lower()
        if any(x in desc for x in ["api", "specification", "spec", "swagger", "openapi"]) and not self.spec_url:
            raise ValidationError(_("Please provide a specification URL for API/spec tasks."))

    # --- main action ---
    def action_submit(self):
        """Create or update a task, apply basic checks, suggest tags, and post message."""
        self.ensure_one()
        self._validate()

        Task = self.env["project.task"]

        # Collect tag names from input + suggestions
        input_tags = []
        if self.tag_names:
            input_tags = [t.strip() for t in self.tag_names.split(",") if t.strip()]

        suggested = self._suggest_tags(self.description)
        all_tags = sorted(set(input_tags) | set(suggested))

        if self.mode == "create":
            vals = {
                "project_id": self.project_id.id,
                "name": self.name,
                "description": self.description,
                "user_ids": [(6, 0, [self.user_id.id])],
                "date_deadline": self.date_deadline,
                "priority": self.priority,
            }
            task = Task.create(vals)
            # Link AI tags
            self._tag_records(task, all_tags)
            # Store AI feedback + status reset
            task.write({
                "ai_feedback": _("Task created via AI wizard. Suggested tags: %s") % ", ".join(all_tags or []),
                "ai_status": False,
            })
            task.message_post(body=_("AI Wizard: Task created."))
            return {"type": "ir.actions.act_window_close"}

        # change mode
        if not self.task_id:
            raise ValidationError(_("Select a task to change."))
        updates = {
            "project_id": self.project_id.id,
            "name": self.name,
            "description": self.description,
            "user_ids": [(6, 0, [self.user_id.id])],
            "date_deadline": self.date_deadline,
            "priority": self.priority,
        }
        self.task_id.write(updates)
        self._tag_records(self.task_id, all_tags)
        self.task_id.write({
            "ai_feedback": _("AI Wizard: Task updated. Suggested tags: %s") % ", ".join(all_tags or []),
        })
        self.task_id.message_post(body=_("AI Wizard: Task updated."))
        return {"type": "ir.actions.act_window_close"}
