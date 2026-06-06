from invoke.tasks import task
from invoke.context import Context


@task(help={"fix": "Reformat code instead of just checking."})
def check_format(ctx: Context, fix: bool = False):
    """Check if code is well formatted."""
    ctx.run(f"ruff format --line-length=120 {'--check' if not fix else ''}")


@task(help={"fix": "Fix all fixable errors instead of just checking."})
def check_lint(ctx: Context, fix: bool = False):
    """Perform static code analysis."""
    ctx.run(f"ruff check --exclude api.py {'--fix' if fix else ''}")
    ctx.run("mypy flatfs")


@task
def check_tests(ctx: Context):
    """Run all tests."""
    ctx.run("pytest")


@task(
    help={
        "report": "Report type. Run `pytest --help` for more details. Default: term",
        "fail_under": "Set minimum required code coverage in %. Default: 95%",
    }
)
def check_coverage(ctx: Context, report: str = "term", fail_under: int = 95):
    """Run all tests with coverage enabled."""
    ctx.run(f"pytest --cov=flatfs --cov-branch --cov-report={report} --cov-fail-under={fail_under}")


@task(help={"fix": "Fix all fixable errors instead of just reporting them."})
def check(ctx: Context, fix: bool = False):
    """Run all checks."""
    ctx.run(f"inv check-format {'--fix' if fix else ''}")
    ctx.run(f"inv check-lint {'--fix' if fix else ''}")
    ctx.run("inv check-tests")
    ctx.run("inv check-coverage")


@task(help={"port": "The port number to use. Default: 8888"})
def serve_coverage(ctx: Context, port: int = 8888):
    """Generate coverage report in HTML format and serve it locally."""
    ctx.run("inv check-coverage --report html:reports/coverage/html --fail-under 0")
    ctx.run(f"python -m http.server {port} --directory reports/coverage/html")


@task
def clean(ctx: Context):
    """Clean project from all .pyc and other generated files."""
    ctx.run("git clean -xdf")


@task
def bump(ctx: Context):
    """Bump project version."""
    ctx.run("bumpify bump")
