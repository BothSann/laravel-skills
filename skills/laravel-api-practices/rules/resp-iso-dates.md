# resp-iso-dates

**CRITICAL.** Dates leave the API as ISO-8601 strings in UTC, such as `2026-11-12T16:12:28.000000Z`. Keep `app.timezone` as `UTC`, cast date columns, and pass the Carbon value to the resource. Laravel serializes it for you.

Avoid:
```php
'created_at' => $this->created_at->format('d/m/Y H:i'),
'created_at' => $this->created_at->diffForHumans(),
```

Do:
```php
'created_at' => $this->created_at,
```

The client formats dates for its user's time zone and language. For a date with no time, such as a birthday, cast it as `date:Y-m-d` so no time zone shift can change the day.

Source: https://laravel.com/docs/13.x/eloquent-serialization#date-serialization
