# Module structure

```text
Modules/<Module>/
  app/
    Contracts/        # public: one API interface, readonly DTOs, enums the DTOs use
    Events/           # public: events carry IDs or DTOs, never models
    Http/             # Controllers, Requests, Resources
    Services/         # business logic; one service implements the API interface
    Repositories/     # only if the project uses a repository package
    Models/
    Listeners/ Jobs/ Policies/ Providers/
  database/           # migrations, factories, seeders
  routes/api.php      # prefixed api/v1
  tests/              # Feature, Unit
  module.json
```

In `config/modules.php`, under `paths.generator`, set `interfaces` to `app/Contracts` and `resource` to `app/Http/Resources`. Then `module:make-interface` and `module:make-resource` write to the right folders.

Request flow: Controller → FormRequest → Service → Repository (if used) → Model, with an API Resource for output.

## The boundary

Everything in `Contracts/` and `Events/` is public. Everything else is private to its module.

| Code in | May depend on |
|---|---|
| A module's private code | Its own public code, and the public code of modules in its `boundaries.uses` |
| A module's `Contracts/` and `Events/` | Only the public code of modules it uses, never its own private code |
| The host `app/` | Any module's public code |

Declare dependencies in the module's `module.json`, then run `sync`:

```json
"boundaries": { "uses": ["Account"] }
```

Cycles are refused. If two modules need each other, move the shared part into a third module or use an event.

## Module communication

Use the first that fits:
1. **Contract, for reads and commands that need an answer.** The owning module defines an interface and DTOs in `Contracts/`, implements the interface in a service, and binds it in its service provider. Other modules type-hint the interface.
2. **Event, for side effects.** The owning module dispatches an event from `Events/`. Other modules register listeners. The owner never knows who listens.

## Data

- Each module owns its tables. Other modules never query them or use their models.
- Store the other module's ID in a plain column. A foreign key constraint in the migration is allowed.
- Don't define Eloquent relationships across modules. To load related data, collect the IDs and call a batch method on the contract, such as `findMany(array $ids)`, so there is one query and no N+1.

## Opting out for one class

An existing app may need to keep sharing a model. The owning module lists it, relative to its namespace:

```json
"boundaries": { "exposes": ["Models\\User"] }
```

Modules that use the owner may then depend on that class. Add an entry only when the owner asks for it.
