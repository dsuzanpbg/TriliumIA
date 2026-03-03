# Project Templates Reference

This file documents all available templates in the project.

## Available Templates

| Template | File | Purpose |
|----------|------|---------|
| Task Request | `TEMPLATE-TASK.md` | Assign project tasks |
| Roadmap | `TEMPLATE-ROADMAP.md` | Project planning and milestones |
| Bug Report | `TEMPLATE-BUG-REPORT.md` | Report and track bugs |
| User Story | `TEMPLATE-USER-STORY.md` | Define user requirements |
| Meeting Notes | `TEMPLATE-MEETING-NOTES.md` | Document meetings |

## Template Usage

### Creating a New Task
1. Copy `TEMPLATE-TASK.md`
2. Fill in all required fields
3. Assign to team member
4. Track in project board

### Creating a User Story
1. Copy `TEMPLATE-USER-STORY.md`
2. Use format: "As a [role], I want [feature], so that [benefit]"
3. Define clear acceptance criteria
4. Estimate story points

### Reporting a Bug
1. Copy `TEMPLATE-BUG-REPORT.md`
2. Include steps to reproduce
3. Add screenshots/logs
4. Assign to developer

### Planning a Meeting
1. Copy `TEMPLATE-MEETING-NOTES.md`
2. Set agenda beforehand
3. Assign roles (facilitator, notes)
4. Track action items

## Template Fields

### Task Fields
- ID (auto-generated)
- Title
- Project
- Creation date
- Due date (optional)
- Priority: Alta/Media/Baja
- State: Pendiente/En Progreso/Completada/Cancelada

### User Story Fields
- ID (US-XXX)
- Title
- Project
- Sprint
- Epic (if applicable)
- Priority
- Story Points: 1/2/3/5/8/13
- State

### Bug Report Fields
- ID (BUG-XXX)
- Title
- Project
- Detection date
- Severity: Critica/Alta/Media/Baja
- Priority: P1/P2/P3/P4

## Naming Conventions

### IDs
- Tasks: TASK-XXX
- User Stories: US-XXX
- Bugs: BUG-XXX
- Meetings: MEET-XXX-YYYY
- Epics: EPIC-XXX

### Example
```
TASK-001: Implement login
US-001: User authentication
BUG-001: Login returns 500 error
MEET-001-2026: Sprint planning
```

## State Workflow

### Tasks
```
Backlog -> Ready -> In Progress -> In Review -> Done
                      or
                   -> Canceled
```

### User Stories
```
Backlog -> Ready -> In Progress -> Done
                     or
                  -> Cancelled
```

### Bugs
```
Reported -> Assigned -> In Progress -> Fixed -> Verified -> Closed
                                                    or
                                                  -> Reopened
```

---

*Last updated: 2026-02-28*
