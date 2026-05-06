from invoke.tasks import task
from invoke.context import Context


@task
def format(ctx: Context):
    """Format code using Black."""
    ctx.run("ruff format --line-length=120")


@task
def coverage(ctx: Context):
    """Check code coverage."""
    ctx.run("pytest --cov-branch --cov=flatfs")


@task
def lint(ctx: Context):
    """Run static code analyzer."""
    ctx.run("ruff check --exclude api.py")


@task
def test(ctx: Context):
    """Run all tests."""
    ctx.run("pytest")


@task(lint, test)
def check(ctx: Context):
    """Run all checks."""
