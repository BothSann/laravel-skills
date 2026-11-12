# auth-sanctum-tokens

**HIGH.** Issue each Sanctum token with the abilities it needs and an expiry date, check the ability on the route, and delete the token on logout. A token with `['*']` and no expiry is a permanent password.

Avoid:
```php
$token = $user->createToken('app')->plainTextToken;
```

Do:
```php
$token = $user->createToken('phone', ['posts:write'], now()->addDays(30))->plainTextToken;
```

```php
Route::post('/posts', [PostController::class, 'store'])
    ->middleware(['auth:sanctum', CheckAbilities::class.':posts:write']);
```

```php
$request->user()->currentAccessToken()->delete();
```

Schedule `sanctum:prune-expired --hours=24` daily. Return the plain-text token once and never log it. An ability says what the token may do. A policy still decides whether this user may do it to this record.

Source: https://laravel.com/docs/13.x/sanctum#token-abilities
