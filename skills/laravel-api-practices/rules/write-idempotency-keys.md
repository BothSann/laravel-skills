# write-idempotency-keys

**HIGH.** A POST that creates something or moves money accepts an `Idempotency-Key` header, so a client that retries after a timeout doesn't create it twice. Store the key on the row with a unique index, and let the database settle the race.

```php
$table->string('idempotency_key')->nullable();
$table->unique(['user_id', 'idempotency_key']);
```

Avoid:
```php
if (! Post::where('idempotency_key', $key)->exists()) {
    $post = Post::create($attributes);
}
```

Do:
```php
$post = Post::createOrFirst(
    ['user_id' => $data->userId, 'idempotency_key' => $data->idempotencyKey],
    ['body' => $data->body],
);

return PostResource::make($post)
    ->response()
    ->setStatusCode($post->wasRecentlyCreated ? 201 : 200);
```

`createOrFirst()` inserts, and on a unique violation returns the existing row. A check followed by an insert lets two requests both pass the check.

Source: https://laravel.com/docs/13.x/eloquent#retrieving-or-creating-models
