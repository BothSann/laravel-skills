# contract-public-ids

**MEDIUM-HIGH.** Use a ULID as the ID of any record whose ID appears in a URL, where a sequential number would reveal how many exist or let someone walk through them. Sequential IDs stay fine for rows that never leave the app.

Avoid, for a public resource:
```php
$table->id();
```

Do:
```php
$table->ulid('id')->primary();
$table->foreignUlid('post_id')->constrained();
```

```php
class Post extends Model
{
    use HasUlids;
}
```

ULIDs sort by creation time, so they index well and work as a cursor. Choose before the first migration ships: changing a primary key later means rewriting every foreign key. An unguessable ID is not authorization. Policies still apply.

Source: https://laravel.com/docs/13.x/eloquent#uuid-and-ulid-keys
