from typing import TYPE_CHECKING, Tuple

from django.db.models import Lookup

if TYPE_CHECKING:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models.sql.compiler import SQLCompiler


class NotEqual(Lookup):  # type: ignore
    lookup_name = "ne"

    def as_sql(  # type: ignore
        self, compiler: "SQLCompiler", connection: "BaseDatabaseWrapper"
    ) -> Tuple[str, str]:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params  # type: ignore
        return "{} <> {}".format(lhs, rhs), params  # type: ignore
