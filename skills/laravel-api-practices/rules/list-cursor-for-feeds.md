# list-cursor-for-feeds

**CRITICAL.** Use `cursorPaginate()` for feeds, timelines, and any large list that clients scroll. `paginate()` counts every row and uses `OFFSET`, which gets slower on each page and repeats or skips rows when new ones arrive.

Avoid:
```php
Post::query()->latest()->paginate(20);
```

Do:
```php
Post::query()->orderByDesc('id')->cursorPaginate(20);
```

The order must be unique, so end it with the primary key, and those columns need an index. The response carries `meta.next_cursor`; the client sends it back as `?cursor=`. There are no page numbers or totals.

Keep `paginate()` where users jump to a numbered page, such as an admin table.

Source: https://laravel.com/docs/13.x/pagination#cursor-pagination
