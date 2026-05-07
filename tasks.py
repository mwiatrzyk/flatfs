from invoke.tasks import task
from invoke.context import Context


@task
def format(ctx: Context):
    """Run code formatter."""
    ctx.run("ruff format . --line-length=120")


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


@task(help={"port": "The port number to use. Default: 8888"})
def serve_coverage(ctx: Context, port: int = 8888):
    """Generate coverage report in HTML format and serve it locally."""
    ctx.run("inv check-coverage --report html:reports/coverage/html --fail-under 0")
    ctx.run(f"python -m http.server {port} --directory reports/coverage/html")


@task
def check_formatting(ctx: Context):
    """Check if code is formatted."""
    ctx.run("ruff format . --line-length=120 --check")


@task
def check_lint(ctx: Context):
    """Perform static code analysis."""
    ctx.run("ruff check --exclude api.py")
    ctx.run("mypy flatfs")


@task(check_formatting, check_lint, check_tests, check_coverage)
def check(ctx: Context):
    """Run all checks."""


@task
def clean(ctx: Context):
    """Clean project from all .pyc and other generated files."""
    ctx.run("git clean -xdf")
