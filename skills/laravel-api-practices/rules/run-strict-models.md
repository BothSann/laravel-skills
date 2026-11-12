# run-strict-models

**MEDIUM.** Turn on Eloquent's strict mode everywhere except production. It turns three silent mistakes into exceptions during development and tests: lazy loading a relationship, filling an attribute that isn't fillable, and reading an attribute that wasn't selected.

```php
// AppServiceProvider::boot()
Model::shouldBeStrict(! $this->app->isProduction());
```

Avoid working around an exception it raises:
```php
Model::preventLazyLoading(false);
```

Do fix the cause:
```php
Post::query()->with('user')->get();
```

In production the same mistakes are logged or ignored instead of thrown, so a missed case can't take a request down.

Source: https://laravel.com/docs/13.x/eloquent#configuring-eloquent-strictness
