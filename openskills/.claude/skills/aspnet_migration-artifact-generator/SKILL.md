# Migration Artifact Generator Skill

---
name: migration-artifact-generator
description: Analyzes ASP.NET applications and generates migration documentation artifacts (PRP, ARCHITECTURE, AGENTS, CODING_STANDARDS, DESIGN_PATTERNS, MIGRATION_MAPPING, API_CONTRACTS, VALIDATION_CHECKLIST) to support AI-assisted migration to Angular/.NET Core.
---

## Purpose
Analyzes existing ASP.NET applications and generates comprehensive migration documentation artifacts required for AI-assisted migration to Angular/.NET Core.

## When to Use
- Starting a new ASP.NET to Angular/.NET Core migration project
- Need to create standardized documentation for AI coding agents
- Updating migration documentation after architecture changes

## Instructions

### Step 1: Codebase Analysis
1. Request user to provide project root path or upload codebase
2. Analyze the following:
   - Solution structure (.sln files, project references)
   - ASP.NET pages (.aspx, .ascx files)
   - Code-behind files (.aspx.cs, .ascx.cs)
   - Business logic layers (App_Code, Services)
   - Data access layer (ADO.NET, Entity Framework usage)
   - Web.config settings (connection strings, authentication)
   - Third-party dependencies (NuGet packages, DLLs)
   - Database schema (if SQL scripts available)

### Step 2: Generate Artifacts
Based on analysis, generate the following files:

#### PRP.md (Project Requirements Prompt)
- Business context from existing application purpose
- Current architecture overview with component diagram
- Feature inventory with migration priority
- Target Angular/.NET Core architecture
- Acceptance criteria per feature
- Technical constraints and requirements

**Template Variables**:
- {{project_name}}
- {{current_dotnet_version}}
- {{target_angular_version}}
- {{target_dotnet_core_version}}
- {{feature_list}}
- {{database_schema_overview}}

#### ARCHITECTURE.md
- Current 3-tier/N-tier architecture diagram
- ASP.NET page lifecycle and state management
- Target SPA architecture (Angular frontend + API backend)
- Separation of concerns (presentation, business, data layers)
- Authentication/authorization flow transformation
- API design (RESTful endpoints, DTOs)

#### AGENTS.md
- Define specialized agents:
  - **Frontend Migration Agent**: ASP.NET pages → Angular components
  - **Backend API Agent**: Business logic → .NET Core services/controllers
  - **Database Migration Agent**: Schema updates, EF Core mappings
  - **Testing Agent**: Unit/integration test generation
  - **Review Agent**: Code quality validation
- Agent interaction protocols
- Validation checkpoints per agent

#### CODING_STANDARDS.md
- C# .NET Core conventions (from existing code style)
- TypeScript/Angular standards
- Naming conventions detected from current codebase
- File organization structure
- Async/await patterns for .NET Core

#### DESIGN_PATTERNS.md
- Patterns detected in current application
- Recommended patterns for Angular (Component, Service, Observable)
- Backend patterns (Repository, Unit of Work, Dependency Injection)
- Include code examples for each pattern

#### MIGRATION_MAPPING.md
- Map each .aspx page to Angular component structure
- Map code-behind logic to API controllers
- Map server controls to Angular Material components
- ViewState → Angular state management mapping
- Session management → JWT/token-based auth

#### API_CONTRACTS.md
- Generate API endpoint specifications from business logic
- Define DTOs for request/response models
- Authentication requirements
- Error handling standards

#### VALIDATION_CHECKLIST.md
- Functional correctness criteria
- Security validation points
- Performance benchmarks
- Code quality thresholds
- Testing coverage requirements

### Step 3: User Validation
1. Present generated artifacts to user
2. Ask clarifying questions for missing information
3. Iterate on feedback
4. Finalize and save all artifacts to project root

## Examples

**Input**: ASP.NET WebForms e-commerce application with product catalog, shopping cart, checkout
**Output**: Complete set of 8 migration artifacts with specific mappings for each page/component

## Tool Permissions
- Read files: Yes (analyze codebase)
- Write files: Yes (generate artifacts)
- Execute code: Yes (run analysis scripts)

## Success Criteria
- All 8+ core artifacts generated
- Artifacts are specific to the analyzed project (not generic)
- Clear migration mappings provided
- Validation checklist aligned with project requirements
