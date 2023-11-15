# pytest-store
Rerun whole testsuites for a certain time or amount

_Still under development._

## Arguments

**`--store-type <pl|pd|list-dict|none>`**  
Set store type (default: installed extra)

**`--store-save <path>`**  
Save file to path, format depends on the ending unless specified.

**`--store-save-format <format>`**  
Save format, depends on store type.

**`--store-save-force`**  
Overwrite existing file

> **NOTE:** All arguments can also be set as environment variables, e.g. `RERUN_TIME="1 hour"`, or _ini_ option, e.g. `rerun_time="10 min"`.

## Examples

```shell
# save results as polars and export to excel
pytest --store-type pl --store-save results.xls examples  
```

## Installation

You can install `pytest-store` via [pip] from [PyPI] or this [repo]:

```shell
pip install pytest-store[<extra>] # extras = "all", "pandas", "polars", "database", "excel", "parquet"
pip install pytest-store[polars,excel,database]
pip install git+git@github.com:TBxy/pytest-store.git@main # latest version
pip install pytest-store --all-extras # development
```

## Todos

* SQL backend, which saves as stream
* Write tests
* Github Actions

## Contributing

Contributions are very welcome. 
Tests are not ready at the moment, use the example scripts.
<!-- Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request. -->

## License

Distributed under the terms of the [MIT] license, `pytest-store` is free and open source software


## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[repo]: https://github.com/TBxy/pytest-store
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@hackebrot]: https://github.com/hackebrot
[MIT]: http://opensource.org/licenses/MIT
[cookiecutter-pytest-plugin]: https://github.com/pytest-dev/cookiecutter-pytest-plugin
[file an issue]: https://github.com/TBxy/pytest-store/issues
[pytest]: https://github.com/pytest-dev/pytest
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/project/pytest-store

----

This [pytest] plugin was generated with [Cookiecutter] along with [@hackebrot]'s [cookiecutter-pytest-plugin] template.


