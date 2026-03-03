# Project Conventions

## Coding Standards

### General Rules
- Language: Spanish for comments/docs, English for code/variables
- **No emojis**: Text-only, no emoji icons anywhere
- Use meaningful names
- Keep functions small and focused
- Write tests for business logic

### File Naming
- Use kebab-case: `user-service.ts`
- Components: PascalCase: `UserProfile.tsx`
- Tests: `.test.ts` or `.spec.ts` suffix

### Code Style
- Use TypeScript with strict mode
- ESLint + Prettier for formatting
- 2 spaces for indentation
- Trailing commas
- Single quotes for strings

## Git Conventions

### Branch Naming
```
feature/TASK-XXX-description
bugfix/TASK-XXX-description
hotfix/TASK-XXX-description
```

### Commit Messages
```
type(scope): description

- TASK-XXX: Task reference
```

Types: feat, fix, docs, style, refactor, test, chore

### Example
```
feat(auth): add login endpoint

- TASK-001: Add JWT authentication
- TASK-002: Add password hashing
```

## Project Structure

```
src/
  api/          # API routes/endpoints
  components/   # UI components
  services/     # Business logic
  models/       # Data models/types
  utils/        # Helper functions
  hooks/        # Custom React hooks
  context/      # React context providers
  domain/       # DDD Domain layer (entities, value-objects)
```

## DDD Structure (Optional)

When using Domain-Driven Design:

```
src/domain/
  [bounded-context]/
    entities/
    value-objects/
    services/
    repositories/
```

## Documentation Rules

### README
- Keep it updated
- Include setup instructions
- Document environment variables

### Code Comments
- Explain WHY, not WHAT
- Use JSDoc for functions
- Document complex logic

### README Template Sections
1. Description
2. Installation
3. Configuration
4. Usage
5. API Reference (if applicable)
6. Contributing

## API Design

### RESTful Principles
- Use HTTP methods correctly: GET, POST, PUT, DELETE
- Use plural nouns: `/users`, `/posts`
- Return appropriate status codes

### Response Format
```json
{
  "data": {},
  "message": "Success",
  "meta": {}
}
```

### Error Format
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": []
}
```

## Testing

### Unit Tests
- Test business logic
- Use describe/it pattern
- Aim for 80% coverage

### Integration Tests
- Test API endpoints
- Test user flows

### Test Naming
```
describe: [function/component] should [behavior]
it: when [condition] then [expected]
```

## Security

- Never commit secrets
- Use environment variables
- Sanitize inputs
- Validate data
- Use HTTPS

## Performance

- Lazy load components
- Memoize expensive calculations
- Optimize images
- Monitor bundle size

---

*Last updated: 2026-02-28*
