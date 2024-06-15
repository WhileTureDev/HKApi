# Database Schema

## Users Table
- **Columns**:
  - `id` (Integer, Primary Key)
  - `username` (String, Unique, Index)
  - `full_name` (String, Index)
  - `email` (String, Unique, Index)
  - `hashed_password` (String, Nullable=False)
  - `created_at` (DateTime, Default=datetime.utcnow)
  - `updated_at` (DateTime, Default=datetime.utcnow)
  - `disabled` (Boolean, Default=False)

## Projects Table
- **Columns**:
  - `id` (Integer, Primary Key)
  - `name` (String, Index, Nullable=False)
  - `description` (String)
  - `created_at` (DateTime, Default=datetime.utcnow)
  - `updated_at` (DateTime, Default=datetime.utcnow)
  - `owner_id` (Integer, ForeignKey('users.id'), Nullable=False)

## Namespaces Table
- **Columns**:
  - `id` (Integer, Primary Key, Index)
  - `name` (String, Index, Nullable=False)
  - `project_id` (Integer, ForeignKey('projects.id'))
  - `created_at` (DateTime, Default=datetime.utcnow)
  - `updated_at` (DateTime, Default=datetime.utcnow)

## Deployments Table
- **Columns**:
  - `id` (Integer, Primary Key, Index)
  - `project` (String, Index)
  - `install_type` (String, Index)
  - `chart_name` (String, Index)
  - `chart_repo_url` (String, Index)
  - `namespace_id` (Integer, ForeignKey('namespaces.id'))
  - `namespace_name` (String, Index)
  - `values` (JSON)
  - `revision` (Integer)
  - `active` (Boolean, Default=True)
  - `status` (String, Default="active")
  - `created_at` (DateTime, Default=datetime.utcnow)
  - `updated_at` (DateTime, Default=datetime.utcnow)
  - `owner_id` (Integer, ForeignKey('users.id'))
