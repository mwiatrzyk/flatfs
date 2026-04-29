import sys

from invoke.tasks import task
from invoke.context import Context

_py_ver = sys.version_info


@task
def format(ctx: Context):
    """Format code using Black."""
    ctx.run(f"black . --line-length=120 --target-version=py{_py_ver.major}{_py_ver.minor}")


@task
def check(ctx: Context):
    """Run all checks."""
    ctx.run("pytest")
