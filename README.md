# Project AI Tasks

**Project AI Tasks** is a custom Odoo module that adds an AI-powered chat panel (bottom-right corner) to help manage project tasks via smart commands.  
It enables PMs and Developers to interact with the system directly from the chat — create, edit, complete, reassign tasks, and more.

---

## 🔧 Installation

1. Copy the `project_ai_tasks` directory into your Odoo `addons/` folder.
2. Restart the Odoo server.
3. Update the Apps list.
4. Search for **Project AI Tasks** in the Apps menu and install it.
5. Assign appropriate access groups to users:
   - `AI Project Manager` (`project_ai_tasks.group_ai_pm`)
   - `AI Developer` (`project_ai_tasks.group_ai_dev`)

---

## 👥 Roles & Permissions

- **AI Project Manager**:
  - Can create, edit, approve, return, cancel, pause, resume, reassign, and comment on tasks.
- **AI Developer**:
  - Can complete tasks, add comments, and return tasks to the PM.
  - Cannot change the project or edit other users' tasks.

---

## 💬 Available Chat Commands

| Command                | Description                              |
|------------------------|------------------------------------------|
| `/create_task`         | Open task creation wizard                |
| `/change_task <id>`    | Open wizard to edit an existing task     |
| `/edit_task <id>`      | Edit a task after feedback               |
| `/complete_task <id>`  | Mark task as completed (by Dev)          |
| `/return_task <id>`    | Return task to PM for rework             |
| `/approve_task <id>`   | Approve a task after return/completion   |
| `/list_tasks`          | Show tasks assigned to the user          |
| `/comment_task <id> text` | Add a comment to the task           |
| `/assign_task <id> @user` | Reassign task to another user        |
| `/cancel_task <id>`    | Cancel the task                          |
| `/pause_task <id>`     | Pause the task                           |
| `/resume_task <id>`    | Resume a paused task                     |
| `/ai_help`             | Show all available commands              |

Chat commands are processed in `mail.channel` or `mail.thread` messages.

---

## ✅ Features Implemented

- AI Chat integration with custom command parser.
- Wizard for creating and updating tasks.
- Built-in validations:
  - Title must contain at least 5 words.
  - Deadline must be between tomorrow and one year from today.
  - Assignee is required.
  - If "API"/"spec" mentioned → specification URL is required.
- Automatic AI tag suggestions (`#bug`, `#api`, `#urgent`, `#feature`) based on task description.
- AI-specific fields on tasks:
  - `ai_status` (Paused, Cancelled, Needs Review)
  - `ai_feedback`
  - `ai_tags`
- Extra buttons on the task form:
  - Pause / Resume / Cancel / Return / Approve / Complete

---

## ⚠️ Limitations / Future Improvements

- No LLM (OpenAI or other) integration yet — tag suggestions are keyword-based.
- No "Edit/Ignore" buttons shown to PM when validation fails — only exceptions are raised.
- `/assign_task` does not check assignee's workload.
- Commands like `/pause_task`, `/comment_task`, `/cancel_task` accept inline text only — no popup forms.
- Chat works inside `mail.channel` panel but does not yet render a custom bottom-right UI widget (e.g., OWL-based bubble).

---

## 📌 How to Use

1. Open any `Discuss` or `Project` chat (bottom-right or in chatter).
2. Type a command like `/create_task`.
3. Follow the link to open the wizard, or perform actions directly via chat.
4. Use role-specific actions depending on whether you are PM or Developer.

---

## 🧾 Metadata

- **Module Name:** `Project AI Tasks`
- **Technical Name:** `project_ai_tasks`
- **Version:** 16.0.1.0.0
- **Author:** Dmytro Stehantsev
- **Category:** Project Management
