<?php

declare(strict_types=1);

namespace EduKit\Support;

use Closure;
use LogicException;
use RuntimeException;

final class Container
{
    /** @var array<string, Closure(self): object> */
    private array $factories = [];

    /** @var array<string, object> */
    private array $instances = [];

    public function set(string $id, callable $factory): void
    {
        $this->factories[$id] = Closure::fromCallable($factory);
        unset($this->instances[$id]);
    }

    public function get(string $id): object
    {
        if (isset($this->instances[$id])) {
            return $this->instances[$id];
        }

        if (!isset($this->factories[$id])) {
            throw new RuntimeException(sprintf('No service is registered for "%s".', $id));
        }

        $instance = ($this->factories[$id])($this);

        if (!is_object($instance)) {
            throw new LogicException(sprintf('The factory for "%s" did not return an object.', $id));
        }

        return $this->instances[$id] = $instance;
    }
}
