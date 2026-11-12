# list-always-paginate

**CRITICAL.** Every endpoint that returns a list paginates it, and the client's page size is validated with an upper limit. An unbounded list works in development and takes the app down once the table grows.

Avoid:
```php
return PostResource::collection(Post::all());
return PostResource::collection(Post::paginate($request->input('per_page')));
```

Do:
```php
// ListPostsRequest
'per_page' => ['sometimes', 'integer', 'between:1,100'],
```

```php
return PostResource::collection(
    Post::query()->latest()->orderBy('id')->paginate($request->integer('per_page', 15))
);
```

A paginator passed to `collection()` adds `links` and `meta` to the response. This also applies to nested lists, such as a post's comments: give them their own paginated endpoint instead of embedding them all.

Source: https://laravel.com/docs/13.x/eloquent-resources#pagination
