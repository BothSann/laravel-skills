# write-dto-input

**HIGH.** Pass a readonly data object from the controller to the service, not the request or a loose array. The service then states exactly what it needs, works the same from a job or a command, and static analysis can check every field.

Avoid:
```php
$this->posts->create($request);
$this->posts->create($request->all());
```

Do:
```php
final readonly class CreatePostData
{
    public function __construct(
        public int $userId,
        public string $body,
        public ?string $idempotencyKey = null,
    ) {}
}
```

```php
$post = $this->posts->create(new CreatePostData(
    userId: $request->user()->id,
    body: $request->validated('body'),
    idempotencyKey: $request->header('Idempotency-Key'),
));
```

Build it only from validated input. Skip it for a single scalar argument.

Source: https://www.php.net/manual/en/language.oop5.properties.php
