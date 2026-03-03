# YAML Structure for Import Tools

## Overview

This document defines the YAML structure used by the import tools (Asana, Trilium). AI agents must follow this structure.

---

## Required Structure

```yaml
# Project (one per file)
project:
  name: "Project Name"
  description: "Brief description"

# Tasks (section creates parent task in Asana)
tasks:
  - name: "Task name"
    section: "Section Name"  # Becomes PARENT task
    due_date: "YYYY-MM-DD"
    assignee: "P1"          # Maps to person_map in config.json
    notes: |
      Detailed description (Markdown supported)
    subtasks:                # Optional extra subtasks
      - "Subtask A"
      - "Subtask B"
```

---

## How It Works

### Asana Import
1. **Section** → Becomes **PARENT task** in Asana
2. **Task** → Becomes **SUBTASK** of the section
3. All parent tasks go to **To Do** column (Agile)
4. Notes stay as **Markdown** (not HTML)

### Structure in Asana
```
Project
└─ To Do (Section)
   ├─ [PARENT] Section Name
   │   ├─ Subtask: Task 1
   │   └─ Subtask: Task 2
   └─ [PARENT] Another Section
       └─ Subtask: Task 3
```

---

## Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `project.name` | Yes | string | Project name |
| `project.description` | No | string | Project description |
| `tasks[].name` | Yes | string | Task title |
| `tasks[].section` | Yes | string | Section name (becomes parent task) |
| `tasks[].due_date` | No | string | ISO date (YYYY-MM-DD) |
| `tasks[].assignee` | No | string | Key from person_map (P1, P2, etc.) |
| `tasks[].notes` | No | string | Description (Markdown) |
| `tasks[].subtasks` | No | list | Extra subtasks as list of strings |

---

## person_map Reference

In `config.json`:
```json
{
  "person_map": {
    "P1": "developer1@company.com",
    "P2": "developer2@company.com"
  }
}
```

---

## Example

```yaml
project:
  name: "My Project"
  description: "Project description"

tasks:
  # Section = becomes PARENT task
  - name: "1.1 First task"
    section: "Infrastructure"
    due_date: "2026-03-01"
    assignee: "P1"
    notes: |
      Description in **Markdown**

  - name: "1.2 Second task"
    section: "Infrastructure"
    due_date: "2026-03-02"
    assignee: "P2"
    notes: |
      Another task

  # Different section = different parent task
  - name: "2.1 Third task"
    section: "Core"
    due_date: "2026-03-03"
    assignee: "P1"
    notes: |
      Task in different section
```

---

## Rules for AI Agents

1. **One project per file**: Each YAML file should contain only one project
2. **Section = Parent**: The `section` field creates a parent task in Asana
3. **All tasks are subtasks**: Tasks under the same section become subtasks of that section parent
4. **Agile sections**: Asana uses To Do, In Progress, Done columns
5. **Assignee keys**: Use P1, P2, P3 (not emails) - mapped in config.json
6. **Due dates**: Use ISO format (YYYY-MM-DD), empty string if TBD
7. **Markdown in notes**: Notes stay as Markdown (not converted to HTML)

---

## File Location

Place YAML files in:
- `unorganizer/` - for project tasks
- Use `.yml` or `.yaml` extension
