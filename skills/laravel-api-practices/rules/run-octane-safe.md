# run-octane-safe

**MEDIUM.** Write code that stays correct when the app boots once and then serves many requests, as it does under Octane and in queue workers. State kept in a static property or a singleton survives into the next request, and may belong to another user.

Avoid:
```php
class Feed
{
    private static array $seen = [];
}

$this->app->singleton(PostService::class, fn ($app) => new PostService($app['request']));
```

Do:
```php
$this->app->scoped(FeedState::class);

$this->app->singleton(PostService::class, fn () => new PostService);
```

Pass the request, the user, and per-request values as method arguments. If a singleton must reach the container, give it a closure that resolves the current one. Use `scoped()` for anything that must reset between requests.

Source: https://laravel.com/docs/13.x/octane#dependency-injection-and-octane
