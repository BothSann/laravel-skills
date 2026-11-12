# write-transactions

**HIGH.** When one operation writes more than one row, wrap the writes in `DB::transaction()`. Without it, a failure halfway leaves data that no code path expects, such as a post without its media rows.

Avoid:
```php
$post = Post::create($attributes);
$post->media()->createMany($media);
```

Do:
```php
$post = DB::transaction(function () use ($attributes, $media) {
    $post = Post::create($attributes);
    $post->media()->createMany($media);

    return $post;
});
```

Put the transaction in the service, not the controller. Keep HTTP calls, file uploads, and mail out of it: they can't be rolled back, and they hold locks while they wait. Pass `attempts: 3` only where deadlocks are expected.

Source: https://laravel.com/docs/13.x/database#database-transactions
