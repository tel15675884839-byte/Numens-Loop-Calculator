from __future__ import annotations

import hmac
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.schemas import (
    AppUpdateConfigRead,
    CalculationRequest,
    CategoryBase,
    CategoryRead,
    DeviceRowBase,
    LoopBase,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from backend.app.services import BackendService
from backend.app.storage import NotFoundError, ProductProtectedError, SQLiteStore, ValidationError
from backend.app.update_config import WINDOWS_CATALOG_UPDATE_MANIFEST_URL, WINDOWS_PROGRAM_UPDATE_MANIFEST_URL

ADMIN_PASSWORD_ENV = "LOOP_CALCULATOR_ADMIN_PASSWORD"
DEFAULT_ADMIN_PASSWORD = "numens888"


def _frontend_dist_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend" / "dist"
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _admin_password() -> str:
    return os.getenv(ADMIN_PASSWORD_ENV) or DEFAULT_ADMIN_PASSWORD


def require_admin(x_admin_password: str | None = Header(default=None, alias="X-Admin-Password")) -> None:
    expected = _admin_password()
    if not x_admin_password or not hmac.compare_digest(x_admin_password, expected):
        raise HTTPException(status_code=403, detail="Administrator access required")


def _default_db_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable)) / "data" / "loop_calculator.sqlite3"
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "backend" / "data" / "loop_calculator.sqlite3"


def _seed_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "products_db.json"
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "products_db.json"


def create_app(db_path: Path | str | None = None, seed_path: Path | str | None = None) -> FastAPI:
    store = SQLiteStore(Path(db_path) if db_path is not None else _default_db_path(), Path(seed_path) if seed_path is not None else _seed_path())
    service = BackendService(store)
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store.initialize()
        yield

    app = FastAPI(title="Loop Calculator Backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.store = store
    app.state.service = service

    def get_service(request: Request) -> BackendService:
        return request.app.state.service

    @app.get("/api/app/update-config", response_model=AppUpdateConfigRead)
    def get_update_config() -> AppUpdateConfigRead:
        return AppUpdateConfigRead(
            platform="windows",
            program_update_manifest_url=WINDOWS_PROGRAM_UPDATE_MANIFEST_URL,
            catalog_update_manifest_url=WINDOWS_CATALOG_UPDATE_MANIFEST_URL,
        )

    @app.get("/api/app/version")
    def get_version() -> dict[str, str]:
        return {"version": "1.0.0", "platform": "windows"}

    @app.post("/api/app/sync-catalog")
    def sync_catalog(
        payload: dict[str, object], service: BackendService = Depends(get_service)
    ) -> dict[str, object]:
        products = payload.get("products", [])
        if not isinstance(products, list):
            raise HTTPException(status_code=422, detail="products must be a list")
        service.store.sync_builtin_products_from_payload(products)
        return {"synced": len(products), "status": "ok"}

    @app.get("/api/projects")
    def list_projects(service: BackendService = Depends(get_service)) -> list[dict[str, object]]:
        return service.store.list_projects()

    @app.post("/api/projects", status_code=status.HTTP_201_CREATED)
    def create_project(project: ProjectCreate, service: BackendService = Depends(get_service)) -> dict[str, object]:
        try:
            return service.store.create_project(project.model_dump(mode="python"))
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str, service: BackendService = Depends(get_service)) -> dict[str, object]:
        try:
            return service.store.get_project(project_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.put("/api/projects/{project_id}")
    def update_project(project_id: str, project: ProjectUpdate, service: BackendService = Depends(get_service)) -> dict[str, object]:
        try:
            return service.store.replace_project(project_id, project.model_dump(mode="python"))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete("/api/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_project(project_id: str, service: BackendService = Depends(get_service)) -> None:
        try:
            service.store.delete_project(project_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/projects/{project_id}/loops", status_code=status.HTTP_201_CREATED)
    def create_loop(project_id: str, loop: LoopBase, service: BackendService = Depends(get_service)) -> dict[str, object]:
        try:
            return service.store.create_loop(project_id, loop.model_dump(mode="python"))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.put("/api/projects/{project_id}/loops/{loop_id}")
    def update_loop(
        project_id: str,
        loop_id: str,
        loop: LoopBase,
        service: BackendService = Depends(get_service),
    ) -> dict[str, object]:
        try:
            return service.store.update_loop(project_id, loop_id, loop.model_dump(mode="python"))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete("/api/projects/{project_id}/loops/{loop_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_loop(project_id: str, loop_id: str, service: BackendService = Depends(get_service)) -> None:
        try:
            service.store.delete_loop(project_id, loop_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/calculations/loop")
    def calculate_loop_endpoint(request: CalculationRequest, service: BackendService = Depends(get_service)) -> dict[str, object]:
        return service.calculate_loop(request)

    @app.post("/api/admin/verify")
    def verify_admin(_: None = Depends(require_admin)) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/products")
    def list_products(
        q: str | None = None,
        category: str | None = None,
        deleted: str = "active",
        service: BackendService = Depends(get_service),
    ) -> list[dict[str, object]]:
        return service.store.list_products(q=q, category=category, deleted=deleted)

    @app.post("/api/products", status_code=status.HTTP_201_CREATED)
    def create_product(
        product: ProductCreate,
        service: BackendService = Depends(get_service),
        _: None = Depends(require_admin),
    ) -> dict[str, object]:
        return service.store.create_product(product.model_dump(mode="python"))

    @app.put("/api/products/{product_id}")
    def update_product(
        product_id: str,
        product: ProductUpdate,
        service: BackendService = Depends(get_service),
        _: None = Depends(require_admin),
    ) -> dict[str, object]:
        try:
            return service.store.update_product(product_id, product.model_dump(mode="python"))
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_product(
        product_id: str,
        force: bool = False,
        service: BackendService = Depends(get_service),
        _: None = Depends(require_admin),
    ) -> None:
        try:
            service.store.delete_product(product_id, force=force)
        except ProductProtectedError as exc:
            raise HTTPException(status_code=409, detail="Built-in products cannot be deleted") from exc
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/products/{product_id}/restore")
    def restore_product(
        product_id: str,
        service: BackendService = Depends(get_service),
        _: None = Depends(require_admin),
    ) -> dict[str, object]:
        try:
            return service.store.restore_product(product_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/categories")
    def list_categories(service: BackendService = Depends(get_service)) -> list[dict[str, object]]:
        return service.store.list_categories()

    @app.post("/api/categories", status_code=status.HTTP_201_CREATED)
    def create_category(
        category: CategoryBase,
        service: BackendService = Depends(get_service),
        _: None = Depends(require_admin),
    ) -> dict[str, object]:
        return service.store.create_category(category.name, category.sort_order)

    frontend_dist = _frontend_dist_path()
    if frontend_dist.is_dir():
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="static-assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = frontend_dist / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(frontend_dist / "index.html")

    return app


app = create_app()
