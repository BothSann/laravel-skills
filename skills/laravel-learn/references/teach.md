# How to teach

Show the idea in plain PHP first when it helps, then what Laravel adds. Use this project's names and real output.

## PHP concepts ledger
`learn/php-concepts.md` holds each idiom once. Search headings with `grep`; don't read the whole file. Add an entry only the first time an idea appears, and link to it afterwards. Keep it plain and short. The comparison line uses `compareWith`; leave it out when that is `null`.

````markdown
## Readonly class
Every property is set once in the constructor and can't change afterwards.
TypeScript: like a class whose fields are all `readonly`, but enforced while the code runs.
```php
final readonly class CreatePostData
{
    public function __construct(public int $userId, public string $body) {}
}
```
Trap: an array or object inside it can still be changed from outside.
Seen in: lesson 03
````

Common traps to cover when they appear:
- Types are checked while the code runs, and scalars are converted silently unless the file declares `strict_types`.
- `==` converts types before comparing; use `===`.
- Arrays are copied on assignment; objects are shared.
- One array type serves as both list and map, and keys keep insertion order.
- `fn` closures capture variables by value automatically; `function` closures need `use`.
- Only double-quoted strings interpolate `$variables`.
- `empty("0")` is true.
- `static` means the class the method was called on; `self` means the class it was written in.
- Each request starts from nothing: no memory is shared between requests unless the app runs under Octane.

## Open the magic once
| Magic | Show it with |
|---|---|
| Service container | Type-hint a class in a controller method and `dd()` it: Laravel built it and its dependencies |
| Facades | `Cache::get()` is `app('cache')->get()`; show `Cache::getFacadeRoot()` in Tinker |
| Route model binding | `{post}` with a `Post $post` parameter: the query runs before the method, and a miss is a 404 |
| Form requests | Send a bad body: the 422 comes before the controller runs |
| Eloquent attributes | `$post->title` isn't a property; show `$post->getAttributes()` in Tinker |
| Eloquent queries | `->toRawSql()`, or `DB::listen()` in a test, shows the real SQL |
| Module providers | `php artisan module:list` and `route:list` show what each module registered |
| Queues | Dispatch a job with `QUEUE_CONNECTION=sync`, then with a worker, and watch when it runs |

## Layers, the first time
| Layer | One line |
|---|---|
| Route | Maps a method and path to a controller, with middleware |
| Form request | Checks who may call and what the input must look like |
| Controller | Reads validated input, calls one service method, returns a resource |
| Service | The steps of the operation, and its transaction |
| Repository | Only if the project uses one: where queries live |
| Model | One table row, its casts and relationships |
| API Resource | The shape of the JSON that leaves the app |
| `Contracts/`, `Events/` | What other modules may use |

## Notes
For "explain in the learn folder", write `learn/notes/<idea>.md`: the question, a plain answer, a small code sample, and one "try it" command, usually for Tinker. Link it from the lesson README.
