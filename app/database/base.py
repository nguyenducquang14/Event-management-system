"""
app/database/base.py
BaseRepository — lớp cha cho tất cả Repository
Chứa logic tái sử dụng: execute query, call procedure, logging, error handling
"""

from __future__ import annotations
import logging
from typing import Any, Optional
from sqlalchemy import text
from app.config import get_db, engine

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Exception tùy chỉnh cho tầng Repository"""
    pass


class BaseRepository:
    """
    Lớp cha trừu tượng cho tất cả Repository.

    Thiết kế:
    - Tất cả method đều là @staticmethod / @classmethod → không cần khởi tạo instance
    - Mỗi method tự quản lý connection qua context manager get_db()
    - Logging đầy đủ: INFO khi thành công, ERROR khi thất bại (kèm SQL)
    - Raise RepositoryError thay vì để exception raw nổi lên tầng UI
    """

    # ── Truy vấn SELECT ──────────────────────────────────────

    @staticmethod
    def execute_query(
        sql: str,
        params: dict | None = None,
        fetch: str = "all",          # "all" | "one" | "none"
    ) -> list[dict] | dict | None:
        """
        Thực thi câu SQL SELECT.

        Args:
            sql:    Câu SQL với placeholder :param_name
            params: Dict tham số {"param_name": value}
            fetch:  "all" → list[dict], "one" → dict|None, "none" → None

        Returns:
            list[dict] khi fetch="all", dict|None khi fetch="one"

        Raises:
            RepositoryError: Khi có lỗi SQL
        """
        try:
            with get_db() as db:
                result = db.execute(text(sql), params or {})
                if fetch == "one":
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                elif fetch == "all":
                    return [dict(r._mapping) for r in result.fetchall()]
                return None
        except Exception as e:
            logger.error(f"[BaseRepository] Query error: {e}\nSQL: {sql}\nParams: {params}")
            raise RepositoryError(f"Lỗi truy vấn dữ liệu: {e}") from e

    @staticmethod
    def execute_dml(
        sql: str,
        params: dict | None = None,
    ) -> int:
        """
        Thực thi câu SQL INSERT / UPDATE / DELETE.

        Returns:
            Số dòng bị ảnh hưởng (rowcount)

        Raises:
            RepositoryError: Khi có lỗi SQL (ví dụ: duplicate key, FK violation)
        """
        try:
            with get_db() as db:
                result = db.execute(text(sql), params or {})
                return result.rowcount
        except Exception as e:
            logger.error(f"[BaseRepository] DML error: {e}\nSQL: {sql}\nParams: {params}")
            raise RepositoryError(f"Lỗi thao tác dữ liệu: {e}") from e

    # ── Gọi Stored Procedure ─────────────────────────────────

    @staticmethod
    def call_procedure(proc_name: str, in_params: list[Any]) -> str:
        """
        Gọi Stored Procedure có OUT parameter kiểu VARCHAR.
        MySQL trả OUT param qua biến @_<proc>_<idx>.

        Args:
            proc_name:  Tên procedure (vd: "sp_register_guest")
            in_params:  Danh sách IN parameters

        Returns:
            Chuỗi kết quả từ OUT parameter cuối cùng

        Raises:
            RepositoryError: Khi lỗi kết nối hoặc procedure không tồn tại
        """
        conn = engine.raw_connection()
        try:
            cur = conn.cursor()
            # Thêm placeholder cho OUT parameter
            all_params = in_params + [""]
            cur.callproc(proc_name, all_params)

            # Lấy OUT param: MySQL đặt tên @_<proc>_<idx_out>
            out_idx = len(in_params)
            cur.execute(f"SELECT @_{proc_name}_{out_idx}")
            row = cur.fetchone()
            conn.commit()

            result = row[0] if (row and row[0] is not None) else "ERROR: Không nhận được phản hồi"
            logger.info(f"[SP] {proc_name}({in_params[:2]}...) → {result[:60]}")
            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"[SP] {proc_name} error: {e}")
            raise RepositoryError(f"Lỗi gọi procedure {proc_name}: {e}") from e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def call_procedure_resultset(proc_name: str, in_params: list[Any]) -> list[dict]:
        """
        Gọi Stored Procedure trả về result set (không có OUT param).
        Dùng cho sp_event_report, sp_get_event_report, ...

        Returns:
            list[dict] các dòng kết quả
        """
        conn = engine.raw_connection()
        try:
            cur = conn.cursor()
            cur.callproc(proc_name, in_params)
            rows = []
            for rs in cur.stored_results():
                cols = [d[0] for d in rs.description]
                rows.extend([dict(zip(cols, r)) for r in rs.fetchall()])
            return rows
        except Exception as e:
            logger.error(f"[SP-RS] {proc_name} error: {e}")
            raise RepositoryError(f"Lỗi gọi procedure {proc_name}: {e}") from e
        finally:
            cur.close()
            conn.close()

    # ── Gọi UDF (User Defined Function) ─────────────────────

    @staticmethod
    def call_function(func_expr: str, params: dict | None = None) -> Any:
        """
        Gọi UDF trong câu SELECT.

        Ví dụ:
            call_function("fn_attendance_rate(:eid)", {"eid": 1})
            call_function("fn_event_balance(:eid)",   {"eid": 1})

        Returns:
            Giá trị trả về của function (float, int, ...)
        """
        sql = f"SELECT {func_expr} AS result"
        row = BaseRepository.execute_query(sql, params, fetch="one")
        return row["result"] if row else None

    # ── Paginate helper ──────────────────────────────────────

    @staticmethod
    def paginate(
        sql: str,
        params: dict | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Phân trang kết quả truy vấn.

        Returns:
            {
                "data":       list[dict],
                "page":       int,
                "page_size":  int,
                "total":      int,
                "total_pages":int,
            }
        """
        count_sql = f"SELECT COUNT(*) AS total FROM ({sql}) AS _sub"
        count_row = BaseRepository.execute_query(count_sql, params, fetch="one")
        total = int(count_row["total"]) if count_row else 0

        offset = (page - 1) * page_size
        paged_sql = f"{sql} LIMIT :_limit OFFSET :_offset"
        paged_params = {**(params or {}), "_limit": page_size, "_offset": offset}
        data = BaseRepository.execute_query(paged_sql, paged_params, fetch="all")

        return {
            "data":        data,
            "page":        page,
            "page_size":   page_size,
            "total":       total,
            "total_pages": max(1, -(-total // page_size)),  # ceiling division
        }
