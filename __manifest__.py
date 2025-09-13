{
    "name": "Project AI Tasks",
    "version": "16.0.1.0.0",
    "author": "Dmytro Stehantsev",
    "category": "Project",
    "depends": ["project", "mail", "contacts"],
    "installable": True,
    "application": True,
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/task_views.xml",
        "views/task_wizard_views.xml",
        "views/ai_chat_views.xml",
    ],
}
