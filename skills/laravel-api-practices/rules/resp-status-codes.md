# resp-status-codes

**CRITICAL.** The status code states the outcome. Clients and retries depend on it.

| Outcome | Code |
|---|---|
| Read or update succeeded | 200 |
| Created | 201, with a `Location` header |
| Succeeded, nothing to return | 204 |
| Not signed in | 401 |
| Signed in, not allowed | 403 |
| Not found, or hidden from this user | 404 |
| Conflicts with current state | 409 |
| Input failed validation | 422 |
| Too many requests | 429 |

```php
return PostResource::make($post)
    ->response()
    ->setStatusCode(201)
    ->header('Location', route('posts.show', $post));
```

```php
$post->delete();

return response()->noContent();
```

Validation, authentication, authorization, and throttling already produce 422, 401, 403, and 429. Don't catch them to return something else.

Source: https://www.rfc-editor.org/rfc/rfc9110#name-status-codes
