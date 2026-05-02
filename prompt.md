# Instructions for Cursor

You are an expert AI developer. Your task is to build out the full Admin Page and Organization Management features for the **OverClocked Appointment App**.

## Context & Architecture
- **Tech Stack**: FastAPI (Python 3.12), PostgreSQL (asyncpg), SQLAlchemy 2.0, React 18, Vite, TypeScript, TailwindCSS.
- **Rules**: Follow the conventions strictly defined in `Agent.md` and `.AI/MVP/PRD.md`. 
- **Existing Admin API**: The backend already has user management and stat endpoints available under `SRC/Backend/routes/admin.py` (e.g., `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/:id/activate`, `GET /api/v1/admin/stats`).

## The Goal
The product owner needs a comprehensive Admin interface that provides system-level monitoring, user control, and a new "Organizations" management tier.

### 1. Admin Dashboard (System-level monitoring)
- **Frontend**: Build a landing page for admins (`/admin`).
- Display key metrics: **Total users**, **Total service providers (organisers)**, and **Total appointments**.
- *Hint*: Use the existing `GET /api/v1/admin/stats` endpoint to fetch this data and build beautiful dashboard tiles.

### 2. User & Provider Management
- **Frontend**: Build a `/admin/users` page.
- **Features**: 
  - View a paginated list of all users.
  - Implement filters (by role, search by name/email, active/inactive).
  - Add actions to activate/deactivate accounts.
  - Add a modal/form to manage and re-assign roles.
- *Hint*: The backend endpoints for these (`GET /users`, `PATCH /users/:id/activate`, `PATCH /users/:id/deactivate`, `PATCH /users/:id/roles`) are already implemented. You just need to build the React frontend and wire them up!

### 3. Organization Management (New Feature Expansion)
The scope has expanded to include explicit "Organization" management.
- **Features to build**:
  - **Organization List Page**: A list of all organizations.
  - **Organization Details Page**: Clicking an organization shows its details (e.g., domain, active users, active instances, etc.).
  - **Organization Actions**: Options to abort, deactivate, report, or manage the organization.
- **Backend Task**: Currently, the system models "service providers" simply as users with the `organiser` role. To support the new requirements, you need to:
  1. **Architect the Data Model**: Either extend the `users` table/organiser role, or (more likely) create a dedicated `organizations` (or `tenants`) table with fields like `domain`, `active_instances`, `status`.
  2. **Implement Backend CRUD**: Create the necessary SQLAlchemy models, generate the Alembic migration, and build the FastAPI routes under `SRC/Backend/routes/organizations.py`.
  3. **Build Frontend**: Build the corresponding React pages and connect them to your new APIs.

## Execution Plan for Cursor
1. **Review**: Briefly read `Agent.md`, `SRC/Backend/routes/admin.py` to understand the current state.
2. **Database & API (Organizations)**: Scaffold the new SQLAlchemy model for Organizations, generate the Alembic migration (`alembic revision --autogenerate`), and build the FastAPI endpoints.
3. **Frontend API Hooks**: Add Axios calls in `SRC/Frontend/src/api/admin.ts` and `src/api/organizations.ts`.
4. **Build UI Components**: Build out the React pages using TailwindCSS, ensuring a premium, modern design. Use `react-router-dom` for navigation between Dashboard, Users, and Organizations.
5. **Testing**: Write unit tests for any new backend logic in `SRC/Backend/tests/unit`, and update API tests as per the project's Definition of Done in `Agent.md`.
