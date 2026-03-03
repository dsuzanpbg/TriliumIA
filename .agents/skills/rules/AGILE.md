# Agile Methodology Skill

## Overview

This project follows Agile/SCRUM methodology for project management and software development.

## SCRUM Events

| Event | Duration | Frequency |
|-------|----------|-----------|
| Daily Standup | 15 min | Daily |
| Sprint Planning | 2-4 hrs | Start of sprint |
| Sprint Review | 1 hr | End of sprint |
| Sprint Retrospective | 1-1.5 hrs | End of sprint |
| Backlog Grooming | 1 hr | Weekly |

## SCRUM Roles

- **Product Owner**: Defines priorities and accepts deliverables
- **Scrum Master**: Facilitates ceremonies, removes blockers
- **Development Team**: Cross-functional, self-organizing

## Sprint Structure

### Sprint Duration
- **Default**: 2 weeks
- **Start**: Monday
- **End**: Friday (previous week)

### Sprint Ceremony Schedule
1. **Monday 09:00**: Sprint Planning
2. **Daily 09:00**: Standup
3. **Friday 16:00**: Review + Retrospective

## Artifacts

### Product Backlog
- Prioritized list of all work
- Product Owner owns this list
- Constantly refined

### Sprint Backlog
- Work committed for current sprint
- Owned by Development Team
- Updated daily

### Increment
- Sum of all completed items
- Must meet Definition of Done

## Definition of Done (DoD)

All items must have:
- [ ] Code in repository
- [ ] Unit tests passing
- [ ] Code review approved
- [ ] Documentation updated
- [ ] Deployed to QA environment
- [ ] QA approved
- [ ] UAT completed (if applicable)

## User Stories

Format: **As a** [role]**, I want** [feature]**, so that** [benefit]

### Story Points
Use Fibonacci sequence: 1, 2, 3, 5, 8, 13

### Acceptance Criteria
Must be:
- Testable
- Observable
- Measurable

## Estimation

### Velocity
- Track historical velocity
- Use last 3 sprints average
- Account for holidays/absences

### Capacity Planning
```
Available days = Team members x Days in sprint
Capacity = Available days - Holidays - Training - Other commitments
```

## Workflow States

| State | Description |
|-------|-------------|
| Backlog | Not prioritized |
| Ready | Prioritized, estimated, ready to start |
| In Progress | Being worked on |
| In Review | Code review, testing |
| Done | Meets DoD, accepted by PO |

## Best Practices

1. Keep sprints consistent in duration
2. Protect sprint scope from changes
3. Remove blockers quickly
4. Update status daily
5. Retrospect and improve continuously

---

*Last updated: 2026-02-28*
