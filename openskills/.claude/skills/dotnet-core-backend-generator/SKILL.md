---
name: dotnet-core-backend-generator
description: Generates .NET Core Web API structure following Clean Architecture principles with controllers, services, repositories, DTOs, entities, validators, and unit tests to accelerate backend migration and scaffold consistent APIs.
---

# .NET Core Backend Structure Generator Skill

## Purpose
Generates .NET Core Web API structure following Clean Architecture principles with controllers, services, repositories, DTOs, entities, and tests.

## When to Use
- Migrating ASP.NET code-behind logic to .NET Core API
- Creating new API endpoints
- Need consistent backend architecture

## Instructions

### Input Requirements
Ask user to provide:
1. **Feature/Domain name** (e.g., Product, Order, User)
2. **Operations needed** (CRUD, custom actions)
3. **Database entity details** (properties, relationships)
4. **Business logic requirements**
5. **Authentication/authorization requirements**
6. **Validation rules**

### Project Structure
Backend/
├── API/
│   ├── Controllers/
│   ├── Middleware/
│   └── Program.cs
├── Application/
│   ├── DTOs/
│   ├── Interfaces/
│   ├── Services/
│   └── Validators/
├── Domain/
│   ├── Entities/
│   └── Interfaces/
├── Infrastructure/
│   ├── Data/
│   ├── Repositories/
│   └── DbContext/
└── Tests/
    ├── UnitTests/
    └── IntegrationTests/

### Generation Process

Templates are provided under `templates/`. Fill placeholders like `{{EntityName}}`, `{{entity_name_kebab}}`, and fields from user input.

## Best Practices Enforced
1. Clean Architecture separation of concerns
2. Result pattern for service responses
3. Async/Await with CancellationToken support
4. Constructor DI for dependencies
5. FluentValidation for DTO validation
6. Soft delete and audit fields
7. Structured logging and Swagger attributes

## Tool Permissions
- Read files: Yes (check existing structure)
- Write files: Yes (generate backend files)
- Execute code: No

## Validation Checklist
- [ ] All layers properly separated
- [ ] Dependency injection configured
- [ ] Async/await with CancellationToken
- [ ] Result pattern implemented
- [ ] Logging in place
- [ ] Unit tests with >80% coverage
- [ ] API documentation attributes
- [ ] Validation rules implemented
- [ ] Error handling comprehensive
