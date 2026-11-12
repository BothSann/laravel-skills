# resp-api-resources

**CRITICAL.** Return an API Resource from every endpoint, never a model or a hand-built array. The resource is the one place that decides which fields leave the app, so a new column can't leak by accident.

Avoid:
```php
return $post;
return response()->json(['id' => $post->id, 'body' => $post->body]);
```

Do:
```php
return PostResource::make($post);
return PostResource::collection($posts);
```

List fields one by one in `toArray()`. Don't use `parent::toArray()` or spread the model's attributes.

Source: https://laravel.com/docs/13.x/eloquent-resources
