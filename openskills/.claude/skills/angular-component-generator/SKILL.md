---
name: angular-component-generator
description: Generates Angular components following migration project standards with TypeScript, HTML templates, styling, and unit tests. Useful for migration from ASP.NET pages to Angular components and for consistent component scaffolding.
---

# Angular Component Generator Skill

## Purpose
Generates Angular components following migration project standards with proper TypeScript, HTML templates, styling, and unit tests.

## When to Use
- Migrating ASP.NET page to Angular component
- Creating new Angular components during migration
- Need consistent component structure across team

## Instructions

### Input Requirements
Ask user to provide:
1. **Component name** (e.g., ProductList, UserProfile)
2. **Component type**:
   - Smart/Container component (with service dependencies)
   - Presentational/Dumb component (input/output only)
   - Layout component
3. **Source ASP.NET page** (optional, for migration mapping)
4. **Required features**:
   - Form handling (Reactive or Template-driven)
   - Data table with pagination/sorting
   - API integration
   - Route parameters
   - State management (standalone, NgRx, signals)

### Generation Process

#### 1. TypeScript Component File (.ts)
See `templates/component.template.ts` for a canonical scaffold using standalone components, `destroy$` pattern, and feature-driven imports.

#### 2. HTML Template (.html)
- Use Angular Material components if specified
- Implement responsive design with flexbox/grid
- Add proper accessibility attributes (ARIA)
- Include loading states and error handling UI

#### 3. SCSS Styling (.scss)
- Use BEM naming convention
- Mobile-first responsive breakpoints
- CSS custom properties for theming
- Component-scoped styles

#### 4. Unit Test (.spec.ts)
See `templates/component.spec.template.ts` for a baseline test that verifies component creation and provides hooks for additional tests.

### Standard Imports by Feature

**Form Handling**:
```
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
```

**HTTP Requests**:
```
import { HttpClient } from '@angular/common/http';
import { catchError, map, finalize } from 'rxjs/operators';
```

**Routing**:
```
import { Router, ActivatedRoute } from '@angular/router';
```

**Angular Material** (if specified):
```
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatButtonModule } from '@angular/material/button';
```

### Best Practices Enforced
1. **Always unsubscribe**: Use takeUntil pattern with destroy$ Subject
2. **Standalone components**: Use Angular 16+ standalone API
3. **Type safety**: Strong typing for all properties and methods
4. **Error handling**: Implement comprehensive error handling for HTTP calls
5. **Loading states**: Include loading indicators for async operations
6. **Accessibility**: WCAG 2.1 AA compliance
7. **Change detection**: Use OnPush strategy when applicable
8. **Signals**: Use Angular 16+ signals for reactive state when specified

## Examples

### Example 1: Data Table Component
**Input**: "Create ProductList component with data table, pagination, sorting, and search"

**Output**:
- Component with MatTable integration
- Paginator and sort functionality
- Search input with debounce
- API service integration
- Loading spinner
- Error handling UI
- Complete unit tests

### Example 2: Form Component
**Input**: "Create UserRegistration component with reactive form validation"

**Output**:
- Reactive form with FormBuilder
- Custom validators
- Real-time validation feedback
- Submit handler with API integration
- Success/error notifications
- Unit tests for validators and submit

## Tool Permissions
- Read files: Yes (check existing components for consistency)
- Write files: Yes (generate component files)
- Execute code: No

## Validation Checklist
Before finalizing component:
- [ ] All imports are correct and minimal
- [ ] Component follows naming conventions
- [ ] Proper lifecycle hooks implemented
- [ ] Unsubscribe pattern in place
- [ ] Type safety throughout
- [ ] Accessibility attributes present
- [ ] Unit tests with >80% coverage
- [ ] No console.log statements
- [ ] Error handling implemented
