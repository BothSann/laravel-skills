# resp-error-shape

**CRITICAL.** Every failure uses Laravel's own JSON shape, so clients parse one format: `message` always, `errors` for validation, and an optional stable `code` for clients to branch on. Don't invent a second envelope.

```json
{ "message": "The body field is required.", "errors": { "body": ["The body field is required."] } }
{ "message": "You have reached the daily post limit.", "code": "post_limit_reached" }
```

Avoid:
```php
return response()->json(['success' => false, 'error' => 'Limit reached'], 200);
```

Do: throw a domain exception that renders itself.
```php
final class PostLimitReached extends RuntimeException
{
    public function render(): JsonResponse
    {
        return response()->json([
            'message' => 'You have reached the daily post limit.',
            'code' => 'post_limit_reached',
        ], 409);
    }
}
```

Never return an error with status 200. Never put exception messages, SQL, or traces in `message`.

Source: https://laravel.com/docs/13.x/errors#renderable-exceptions
