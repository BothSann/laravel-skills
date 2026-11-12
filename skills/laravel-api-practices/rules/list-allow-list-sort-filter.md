# list-allow-list-sort-filter

**CRITICAL.** Validate sort and filter parameters against a fixed list before they reach the query. Query bindings protect values, not column names, so a client-chosen column can sort by a private field or force a slow scan on a column with no index.

Avoid:
```php
Post::query()->orderBy($request->input('sort'))->paginate();
```

Do:
```php
// ListPostsRequest
'sort' => ['sometimes', Rule::in(['created_at', 'likes_count'])],
'status' => ['sometimes', Rule::enum(PostStatus::class)],
```

```php
Post::query()
    ->when($request->validated('status'), fn ($query, $status) => $query->where('status', $status))
    ->orderBy($request->validated('sort', 'created_at'))
    ->orderBy('id')
    ->paginate();
```

Every column on the list needs an index that serves it.

Source: https://laravel.com/docs/13.x/validation#rule-in
