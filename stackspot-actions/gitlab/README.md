# Create Repository Gitlab

Creates a new repository (aka project) in a specific Gitlab group.

## How to set up this project

This project was developed with **Python v3.9**, and it also uses **Python's Virtualenv tool**. So before working on this project we need to set up it.

Inside this project's folder, execute those commands to configure your environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Now, before starting to code, run all unit tests:

```shell
pytest -v
```

If everything is ok, you can code now :-)

> ⚠️ You can also run the unit tests with the standard unittest library, as below:
> ```shell
> python3 -m unittest script_test.py
> ```

For more detail on how to configure Virtualenv, read [this article](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).

## Running tests with coverage

Unfortunately, the feature "run tests with coverage" doesn't work with Pycharm Community Edition, so that you need to run it via command line:

```shell
pytest -v --cov --cov-report=html:.coverage_reports
```

A directory called `.coverage_reports` will be created with all the coverage reports in HTML format inside of it. Then, just open the `index.html` on the browser to see the report details. 

## Adding new dependencies

If you add new dependencies in the project, don't forget to run this command below so that other developers can import the environment in their machines correctly:
```shell
pip freeze > requirements.txt
```