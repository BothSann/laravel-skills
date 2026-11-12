# resp-conditional-relations

**CRITICAL.** Inside a resource, read relationships and counts only through `whenLoaded()` and `whenCounted()`. Touching `$this->user` directly runs one query per row. The query that feeds the resource decides what to load.

Avoid:
```php
'author' => UserResource::make($this->user),
'comments_count' => $this->comments()->count(),
```

Do:
```php
'author' => UserResource::make($this->whenLoaded('user')),
'comments_count' => $this->whenCounted('comments'),
```

```php
return PostResource::collection(
    Post::query()->with('user')->withCount('comments')->paginate()
);
```

A key whose relation wasn't loaded is left out of the response.

Source: https://laravel.com/docs/13.x/eloquent-resources#conditional-relationships
