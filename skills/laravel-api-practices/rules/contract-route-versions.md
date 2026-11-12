# contract-route-versions

**MEDIUM-HIGH.** Put every route under a version prefix from the first release, such as `api/v1`. Adding a field is safe within a version. Removing or renaming a field, changing a type, or changing a status code needs a new version.

```php
Route::prefix('v1')->group(function () {
    Route::apiResource('posts', PostController::class);
});
```

Before removing an endpoint, announce it on every response with the standard headers, so client developers see it in their logs:

```php
$response->headers->set('Deprecation', '@'.$deprecatedAt->timestamp);
$response->headers->set('Sunset', $removedAt->toRfc7231String());
```

Give `v2` its own controllers and resources. Don't branch on the version inside shared code.

Source: https://www.rfc-editor.org/rfc/rfc9745
