from invoke.tasks import task
from invoke.context import Context


@task
def format(ctx: Context):
    """Format code using Black."""
    ctx.run("ruff format --line-length=120")


@task
def build(ctx: Context):
    """Build package for deployment."""
    ctx.run("poetry build")


@task
def bump(ctx: Context):
    """Bump project version."""
    ctx.run("bumpify bump")


@task
def check_coverage(ctx: Context):
    """Check code coverage."""
    ctx.run("pytest --cov-branch --cov=flatfs --cov-fail-under=95")


@task
def check_formatting(ctx: Context):
    """Check if the code is formatted."""
    ctx.run("ruff format --line-length=120 --check")


@task
def check_linter(ctx: Context):
    """Run static code analyzer."""
    ctx.run("ruff check --exclude api.py")


@task
def check_tests(ctx: Context):
    """Run all tests."""
    ctx.run("pytest")


@task(check_formatting, check_linter, check_coverage, check_tests)
def check_all(ctx: Context):
    """Run all checks."""
